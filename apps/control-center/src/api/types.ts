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
  "allowed_preview" | "approval_required" | "blocked";

export type BackendConnectionState =
  "unknown" | "checking" | "online" | "offline" | "degraded" | "mock_fallback";

export interface BackendConnectionSummary {
  state: BackendConnectionState;
  apiBaseLabel: string;
  checkedAt: string;
  safeMessage: string;
  usingMockData: boolean;
  warnings: string[];
}

export type ControlCenterRouteReadStateKind =
  | "backend_owned"
  | "degraded"
  | "mock_fallback"
  | "blocked"
  | "planned";

export interface ControlCenterRouteReadState {
  route: string;
  surfaceLabel: string;
  state: ControlCenterRouteReadStateKind;
  statusLabel: string;
  sourceLabel: string;
  safeSummary: string;
  backendRouteRefs: string[];
  warningRefs: string[];
  blockedAuthorityRefs: string[];
  nextSafeAction: string;
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

export type TurnRouterPreviewSampleId =
  | "diy-desk"
  | "office-memory"
  | "shopping-list"
  | "current-lumber-prices"
  | "order-materials"
  | "card-pickup"
  | "base-answer-bypass";

export interface TurnRouterPreviewRequest {
  sample_id?: TurnRouterPreviewSampleId;
  text?: string;
}

export interface TurnRouterPolicySummary {
  turn_contract: string;
  memory_scope: string;
  memory_read_allowed: boolean;
  memory_write_allowed: boolean;
  tool_policy: string;
  tool_choice: string;
  tool_execution_allowed: boolean;
  action_execution_allowed: boolean;
  workflow_execution_allowed: boolean;
  context_injection_allowed: boolean;
  approval_policy: string;
  approval_required: boolean;
  planner: boolean;
  durable_state: boolean;
  state_policy: string;
  prompt_profile: string;
  output_contract: string;
  runtime_model_call_allowed: boolean;
  provider_call_allowed: boolean;
  shell_subprocess_allowed: boolean;
  browser_network_allowed: boolean;
  connector_write_allowed: boolean;
  side_effects_allowed: boolean;
  execution_ready: boolean;
}

export interface TurnHarnessBindingReadModel {
  contract_ref: "contract-ref:turn-contract-router:harness-binding:v1";
  binding_ref: string;
  decision_ref: string;
  policy_ref: string;
  turn_contract: string;
  safe_summary: string;
  reason_refs: string[];
  evidence_refs: string[];
  risk_flags: string[];
  memory_scope: string;
  memory_touched: boolean;
  reviewed_memory_refs_allowed: boolean;
  memory_content_retrieved: boolean;
  memory_write_allowed: boolean;
  memory_write_performed: boolean;
  tool_policy: string;
  tools_exposed_count: number;
  tool_refs: string[];
  execution_tools_exposed_count: number;
  planner: boolean;
  durable_state: boolean;
  approval_policy: string;
  approval_required: boolean;
  approval_envelope_required: boolean;
  side_effects_allowed: boolean;
  execution_ready: boolean;
  receipt_required: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  raw_memory_body_persisted: boolean;
  raw_local_path_persisted: boolean;
  credential_persisted: boolean;
  safe_refs_only: boolean;
  blocked_authority_refs: string[];
  no_effect_scope: "turn_harness_binding_compilation_only";
  no_runtime_model_call_performed: boolean;
  no_provider_call_performed: boolean;
  no_tool_execution_performed: boolean;
  no_action_execution_performed: boolean;
  no_shell_subprocess_performed: boolean;
  no_browser_network_performed: boolean;
  no_connector_write_performed: boolean;
}

export interface TurnHarnessBindingReceiptSummary {
  contract_ref: "contract-ref:turn-contract-router:harness-binding:v1";
  binding_ref: string;
  decision_ref: string;
  policy_ref: string;
  turn_contract: string;
  safe_summary: string;
  reason_refs: string[];
  evidence_refs: string[];
  risk_flags: string[];
  memory_scope: string;
  memory_touched: boolean;
  reviewed_memory_refs_allowed: boolean;
  memory_content_retrieved: boolean;
  memory_write_allowed: boolean;
  memory_write_performed: boolean;
  tool_policy: string;
  tools_exposed_count: number;
  tool_refs: string[];
  execution_tools_exposed_count: number;
  planner: boolean;
  durable_state: boolean;
  approval_policy: string;
  approval_required: boolean;
  approval_envelope_required: boolean;
  side_effects_allowed: boolean;
  execution_ready: boolean;
  receipt_required: boolean;
  prompt_body_persisted: boolean;
  response_body_persisted: boolean;
  memory_body_persisted: boolean;
  local_path_body_persisted: boolean;
  sensitive_material_persisted: boolean;
  safe_refs_only: boolean;
  blocked_authority_refs: string[];
  no_effect_scope: "turn_harness_binding_compilation_only";
  no_runtime_model_call_performed: boolean;
  no_provider_call_performed: boolean;
  no_tool_execution_performed: boolean;
  no_action_execution_performed: boolean;
  no_shell_subprocess_performed: boolean;
  no_browser_network_performed: boolean;
  no_connector_write_performed: boolean;
}

export interface TurnRouterNoEffectProof {
  authority_granted: boolean;
  execution_permitted: boolean;
  no_runtime_model_call_performed: boolean;
  no_provider_call_performed: boolean;
  no_tool_execution_performed: boolean;
  no_action_execution_performed: boolean;
  no_workflow_execution_performed: boolean;
  no_context_injection_performed: boolean;
  no_memory_content_retrieved: boolean;
  no_memory_write_performed: boolean;
  no_durable_state_write_performed: boolean;
  no_shell_subprocess_performed: boolean;
  no_browser_network_performed: boolean;
  no_connector_write_performed: boolean;
  invocation_policy_compiled_only: boolean;
  raw_request_text_persisted: boolean;
}

export interface TurnRouterPreviewReadModel {
  contract_ref: string;
  preview_ref: string;
  request_ref: string;
  request_kind: "sample" | "ephemeral_text";
  sample_id: TurnRouterPreviewSampleId | null;
  selected_turn_contract: string;
  confidence: number;
  reason_refs: string[];
  risk_flags: string[];
  policy_summary: TurnRouterPolicySummary;
  no_effect_proof: TurnRouterNoEffectProof;
  blocked_authority_refs: string[];
  lane_result_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  route_refs: string[];
  redactions_applied: string[];
  safe_summary: string;
  raw_content_included: boolean;
  ephemeral_request_text_omitted: boolean;
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

export type TrustAuthorityState =
  | "available_now"
  | "approval_required"
  | "planned"
  | "blocked";

export type TrustOperatorPosture =
  | "enabled_read_only"
  | "review_only"
  | "approval_required"
  | "planned"
  | "blocked";

export type TrustAuthorityLaneKind =
  | "read_preview"
  | "draft_proposal"
  | "reversible_local_mutation"
  | "external_mutation"
  | "background_standing_authority";

export interface TrustAuthorityLane {
  lane_ref: string;
  label: string;
  tier: number;
  tier_id: string;
  tier_label: string;
  lane_kind: TrustAuthorityLaneKind;
  authority_state: TrustAuthorityState;
  authority_state_label: string;
  operator_posture: TrustOperatorPosture;
  current_posture: string;
  approval_posture: string;
  operator_can_do_now: string;
  next_safe_action: string;
  route_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  docs_refs: string[];
  cli_inspection_refs: string[];
  safe_disable_refs: string[];
  rollback_refs: string[];
  promotion_path_refs: string[];
  blocked_authority_refs: string[];
  requires_exact_approval: boolean;
  requires_safe_disable: boolean;
  requires_rollback_posture: boolean;
  rollback_execution_enabled: boolean;
  safe_refs_only: boolean;
  control_center_grants_authority: boolean;
}

export interface TrustAuthorityTierSummary {
  tier: number;
  tier_id: string;
  label: string;
  available_now_count: number;
  approval_required_count: number;
  planned_count: number;
  blocked_count: number;
  operator_summary: string;
}

export interface TrustAuthorityMatrix {
  schema_version: "control-center-trust-authority-matrix.v1";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  control_center_grants_authority: boolean;
  doctrine: string;
  operator_summary: string;
  lanes: TrustAuthorityLane[];
  tier_summaries: TrustAuthorityTierSummary[];
  available_now_lane_refs: string[];
  approval_required_lane_refs: string[];
  planned_lane_refs: string[];
  blocked_lane_refs: string[];
  route_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  docs_refs: string[];
  cli_inspection_refs: string[];
  safe_disable_refs: string[];
  rollback_refs: string[];
  promotion_path_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  broad_approval_enabled: boolean;
  standing_authority_enabled: boolean;
  runtime_context_injection_enabled: boolean;
  connector_write_enabled: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export type CodingCockpitAuthorityModeState =
  | "current"
  | "planned"
  | "blocked"
  | "hard_gate";

export type CodingCockpitPanelState =
  | "backend_owned"
  | "read_only"
  | "proposal_only"
  | "preview_only"
  | "blocked"
  | "planned";

export interface CodingCockpitAuthorityMode {
  mode_ref: string;
  label: string;
  state: CodingCockpitAuthorityModeState;
  operator_posture: string;
  safe_summary: string;
  allowed_now: boolean;
  planned: boolean;
  blocked: boolean;
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
}

export interface CodingCockpitRefItem {
  item_ref: string;
  label: string;
  status: string;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
}

export interface CodingCockpitPreviewPanel {
  panel_ref: string;
  title: string;
  state: CodingCockpitPanelState;
  safe_summary: string;
  items: CodingCockpitRefItem[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  mutation_enabled: boolean;
  runtime_authority_enabled: boolean;
}

export interface CodingCockpitSessionReadModel {
  schema_version: "uaa-coding-cockpit-session.v1";
  contract_ref: string;
  route_ref: string;
  session_ref: string;
  workspace_ref: string;
  repo_scope_ref: string;
  branch_ref: string;
  authority_profile_ref: string;
  active_agent_ref: string;
  active_task_ref: string;
  active_context_pack_ref: string;
  active_patch_proposal_ref: string;
  active_command_proposal_ref: string;
  active_git_ref: string;
  active_proof_ref: string;
  active_preview_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  docs_refs: string[];
  cli_inspection_refs: string[];
  status: string;
  task_status: string;
  branch_label: string;
  active_agent_label: string;
  authority_mode: string;
  backend_owned: boolean;
  mock_fallback: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  control_center_grants_authority: boolean;
  full_strength_goal: string;
  repo_safe_scope: string;
  authority_modes: CodingCockpitAuthorityMode[];
  project_model: CodingProjectModelReadModel;
  workspace_context: CodingCockpitPreviewPanel;
  task_thread: CodingCockpitPreviewPanel;
  task_timeline: CodingCockpitPreviewPanel;
  diff_preview: CodingCockpitPreviewPanel;
  proof_preview: CodingCockpitPreviewPanel;
  terminal_preview: CodingCockpitPreviewPanel;
  git_preview: CodingCockpitPreviewPanel;
  test_output_preview: CodingCockpitPreviewPanel;
  live_preview: CodingCockpitPreviewPanel;
  chat_thread: CodingCockpitPreviewPanel;
  same_ref_spine: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export type CodingProjectCapabilityKind =
  | "workspace"
  | "repo"
  | "lane"
  | "branch"
  | "worktree"
  | "files"
  | "diffs"
  | "tests"
  | "preview"
  | "terminal"
  | "git"
  | "proof";

export type CodingProjectCapabilityState =
  | "read_only"
  | "proposal_only"
  | "blocked"
  | "planned";

export interface CodingProjectCapabilityReadModel {
  capability_ref: string;
  label: string;
  capability_kind: CodingProjectCapabilityKind;
  state: CodingProjectCapabilityState;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  browser_automation_enabled: boolean;
  provider_model_call_enabled: boolean;
  background_autonomy_enabled: boolean;
}

export interface CodingProjectModelReadModel {
  schema_version: "uaa-coding-project-model.v1";
  project_model_ref: string;
  session_ref: string;
  workspace_ref: string;
  repo_scope_ref: string;
  branch_ref: string;
  worktree_ref: string;
  lane_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  status: "read_only_project_posture";
  project_label: string;
  repo_label: string;
  branch_label: string;
  worktree_label: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  capabilities: CodingProjectCapabilityReadModel[];
  capability_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  safe_refs_only: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  repo_file_read_performed: boolean;
  project_scan_performed: boolean;
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_status_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  dev_server_control_enabled: boolean;
  browser_preview_enabled: boolean;
  browser_automation_enabled: boolean;
  provider_model_call_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export type CodingContextRefKind =
  | "file"
  | "folder"
  | "exclude_rule"
  | "search_ref";

export type CodingContextRefStatus =
  | "included"
  | "excluded"
  | "candidate"
  | "blocked";

export interface CodingContextRefReadModel {
  context_ref: string;
  label: string;
  ref_kind: CodingContextRefKind;
  status: CodingContextRefStatus;
  include_reason: string;
  token_estimate: number;
  operator_selected: boolean;
  agent_selected: boolean;
  included_in_preview: boolean;
  excluded_from_preview: boolean;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  raw_path_included: boolean;
  raw_content_included: boolean;
}

export interface CodingContextComparisonReadModel {
  comparison_ref: string;
  label: string;
  operator_context_ref: string;
  agent_context_ref: string;
  status: "aligned" | "operator_only" | "agent_only" | "blocked";
  safe_summary: string;
  proof_refs: string[];
}

export interface CodingWorkspaceContextReadModel {
  schema_version: "uaa-coding-workspace-context.v1";
  context_pack_ref: string;
  session_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  status: "read_only_context_pack_preview";
  budget_state: "within_budget" | "near_limit" | "over_limit_blocked";
  token_budget_limit: number;
  token_estimate_total: number;
  token_budget_remaining: number;
  context_refs: CodingContextRefReadModel[];
  operator_selected_refs: string[];
  agent_selected_refs: string[];
  excluded_refs: string[];
  search_refs: string[];
  comparison: CodingContextComparisonReadModel[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  preview_only: boolean;
  safe_refs_only: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  repo_file_read_performed: boolean;
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export type CodingPatchChangeKind =
  | "modify"
  | "add"
  | "delete_blocked"
  | "generated_blocked";

export interface CodingPatchProposalFileReadModel {
  change_ref: string;
  file_ref: string;
  label: string;
  change_kind: CodingPatchChangeKind;
  status: "proposed" | "blocked";
  hunk_refs: string[];
  additions: number;
  deletions: number;
  safe_summary: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  raw_path_included: boolean;
  raw_content_included: boolean;
}

export interface CodingPatchProposalReadModel {
  schema_version: "uaa-coding-patch-proposal.v1";
  patch_proposal_ref: string;
  session_ref: string;
  context_pack_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  status: "proposal_artifact_preview";
  title: string;
  safe_summary: string;
  proposed_file_refs: string[];
  file_changes: CodingPatchProposalFileReadModel[];
  diff_preview_refs: string[];
  diff_summary_lines: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  proposal_only: boolean;
  safe_refs_only: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  repo_file_read_performed: boolean;
  patch_apply_enabled: boolean;
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CodingPatchApplyPrerequisiteReadModel {
  prerequisite_ref: string;
  label: string;
  status: "present" | "missing" | "blocked";
  safe_summary: string;
  evidence_refs: string[];
  blocked_authority_refs: string[];
}

export interface CodingPatchApplyReadinessReadModel {
  schema_version: "uaa-coding-patch-apply-readiness.v1";
  readiness_ref: string;
  session_ref: string;
  context_pack_ref: string;
  patch_proposal_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  unblock_prompt_refs: string[];
  status: "blocked_missing_exact_apply_contract";
  title: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  required_authority_profile_refs: string[];
  prerequisites: CodingPatchApplyPrerequisiteReadModel[];
  expected_receipt_refs: string[];
  rollback_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  readiness_only: boolean;
  safe_refs_only: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  repo_file_read_performed: boolean;
  exact_patch_body_available: boolean;
  hunk_selection_contract_available: boolean;
  checkpoint_contract_available: boolean;
  approval_binding_available: boolean;
  rollback_contract_available: boolean;
  patch_apply_enabled: boolean;
  file_write_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  rollback_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CodingSuggestedTestCommandReadModel {
  command_ref: string;
  label: string;
  command_kind:
    | "focused_pytest"
    | "frontend_test"
    | "lint_typecheck"
    | "repo_verifier";
  status: "suggested_blocked";
  safe_command_summary: string;
  allowlist_ref: string;
  expected_receipt_ref: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  raw_command_included: boolean;
  raw_output_included: boolean;
  command_execution_enabled: boolean;
}

export interface CodingTestCommandReadinessReadModel {
  schema_version: "uaa-coding-test-command-readiness.v1";
  readiness_ref: string;
  session_ref: string;
  context_pack_ref: string;
  patch_proposal_ref: string;
  patch_apply_readiness_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  unblock_prompt_refs: string[];
  status: "blocked_missing_allowlisted_command_authority";
  title: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  allowlist_refs: string[];
  suggested_commands: CodingSuggestedTestCommandReadModel[];
  expected_receipt_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  readiness_only: boolean;
  safe_refs_only: boolean;
  raw_command_included: boolean;
  raw_output_included: boolean;
  command_output_summary_included: boolean;
  exit_code_available: boolean;
  test_receipt_created: boolean;
  command_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  arbitrary_shell_enabled: boolean;
  install_command_enabled: boolean;
  network_command_enabled: boolean;
  destructive_command_enabled: boolean;
  background_process_enabled: boolean;
  file_write_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CodingGitReviewItemReadModel {
  item_ref: string;
  label: string;
  item_kind:
    | "status"
    | "diff"
    | "changed_files"
    | "commit_proposal"
    | "pr_description_proposal";
  status: "blocked" | "proposal_ref";
  safe_summary: string;
  expected_receipt_ref: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  raw_git_output_included: boolean;
  raw_diff_included: boolean;
  raw_path_included: boolean;
  git_mutation_enabled: boolean;
}

export interface CodingGitReviewReadModel {
  schema_version: "uaa-coding-git-review.v1";
  git_review_ref: string;
  session_ref: string;
  context_pack_ref: string;
  patch_proposal_ref: string;
  patch_apply_readiness_ref: string;
  test_command_readiness_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  unblock_prompt_refs: string[];
  status: "blocked_missing_git_review_authority";
  title: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  status_refs: string[];
  changed_file_refs: string[];
  diff_refs: string[];
  commit_proposal_refs: string[];
  pr_description_proposal_refs: string[];
  expected_receipt_refs: string[];
  review_items: CodingGitReviewItemReadModel[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  proposal_only: boolean;
  safe_refs_only: boolean;
  git_status_execution_enabled: boolean;
  git_diff_execution_enabled: boolean;
  stage_enabled: boolean;
  commit_enabled: boolean;
  push_enabled: boolean;
  pr_open_enabled: boolean;
  merge_enabled: boolean;
  raw_git_output_included: boolean;
  raw_diff_included: boolean;
  raw_path_included: boolean;
  commit_message_text_included: boolean;
  pr_description_text_included: boolean;
  git_receipt_created: boolean;
  shell_subprocess_execution_enabled: boolean;
  file_write_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CodingLivePreviewItemReadModel {
  item_ref: string;
  label: string;
  item_kind:
    | "dev_server_status"
    | "preview_url"
    | "screenshot"
    | "console_errors"
    | "visual_regression"
    | "route_checklist"
    | "viewport";
  status: "blocked" | "planned" | "proposal_ref";
  safe_summary: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  raw_url_included: boolean;
  screenshot_included: boolean;
  console_output_included: boolean;
  browser_automation_enabled: boolean;
  dev_server_control_enabled: boolean;
}

export interface CodingLivePreviewReadModel {
  schema_version: "uaa-coding-live-preview.v1";
  live_preview_ref: string;
  session_ref: string;
  context_pack_ref: string;
  patch_proposal_ref: string;
  test_command_readiness_ref: string;
  git_review_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  unblock_prompt_refs: string[];
  status: "blocked_missing_live_preview_authority";
  title: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  dev_server_status_refs: string[];
  preview_url_refs: string[];
  screenshot_refs: string[];
  visual_proof_refs: string[];
  route_checklist_refs: string[];
  viewport_refs: string[];
  console_error_refs: string[];
  preview_items: CodingLivePreviewItemReadModel[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  status_only: boolean;
  safe_refs_only: boolean;
  raw_url_included: boolean;
  raw_console_output_included: boolean;
  screenshot_artifact_included: boolean;
  screenshot_capture_enabled: boolean;
  visual_regression_enabled: boolean;
  console_capture_enabled: boolean;
  dev_server_status_detection_enabled: boolean;
  dev_server_start_enabled: boolean;
  dev_server_stop_enabled: boolean;
  browser_preview_enabled: boolean;
  browser_automation_enabled: boolean;
  browser_interaction_enabled: boolean;
  network_fetch_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  file_write_enabled: boolean;
  git_mutation_enabled: boolean;
  provider_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CodingAgentReviewSlotReadModel {
  agent_slot_ref: string;
  label: string;
  slot_kind:
    | "implementer"
    | "reviewer"
    | "local_verifier"
    | "security_reviewer"
    | "ux_reviewer"
    | "test_fixer"
    | "merge_captain";
  status: "proposal_ref" | "blocked";
  safe_summary: string;
  output_artifact_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  provider_model_call_enabled: boolean;
  local_agent_execution_enabled: boolean;
  background_dispatch_enabled: boolean;
  autonomous_execution_enabled: boolean;
  raw_prompt_included: boolean;
  raw_response_included: boolean;
}

export interface CodingMultiAgentReviewReadModel {
  schema_version: "uaa-coding-multi-agent-review.v1";
  review_ref: string;
  session_ref: string;
  context_pack_ref: string;
  patch_proposal_ref: string;
  test_command_readiness_ref: string;
  git_review_ref: string;
  live_preview_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  unblock_prompt_refs: string[];
  status: "blocked_missing_multi_agent_authority";
  title: string;
  full_strength_goal: string;
  repo_safe_current_state: string;
  safe_summary: string;
  agent_slots: CodingAgentReviewSlotReadModel[];
  plan_artifact_refs: string[];
  review_artifact_refs: string[];
  diff_comparison_refs: string[];
  disagreement_summary_refs: string[];
  handoff_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  proposal_only: boolean;
  safe_refs_only: boolean;
  provider_model_call_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  local_agent_execution_enabled: boolean;
  multi_agent_execution_enabled: boolean;
  background_dispatch_enabled: boolean;
  background_autonomy_enabled: boolean;
  autonomous_execution_enabled: boolean;
  context_injection_enabled: boolean;
  raw_prompt_included: boolean;
  raw_response_included: boolean;
  provider_payload_included: boolean;
  file_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  git_mutation_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export type WorkBoardColumnStatus =
  | "planned"
  | "in_progress"
  | "review"
  | "blocked"
  | "done";

export type WorkBoardCardPriority = "critical" | "high" | "medium" | "low";

export type WorkBoardCardAuthorityState =
  | "enabled_read_only"
  | "proposal_only"
  | "blocked";

export interface WorkBoardBlockedLaneReadModel {
  lane_ref: string;
  label: string;
  safe_summary: string;
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
}

export interface WorkBoardCardReadModel {
  card_ref: string;
  title: string;
  safe_summary: string;
  column_ref: string;
  priority: WorkBoardCardPriority;
  authority_state: WorkBoardCardAuthorityState;
  owner_ref: string;
  progress_label: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocker_refs: string[];
  surface_refs: string[];
  cli_inspection_refs: string[];
  tags: string[];
  raw_path_included: boolean;
  raw_content_included: boolean;
  mutation_enabled: boolean;
  drag_persistence_enabled: boolean;
}

export interface WorkBoardColumnReadModel {
  column_ref: string;
  label: string;
  status: WorkBoardColumnStatus;
  safe_summary: string;
  card_refs: string[];
  wip_limit: number;
  blocked_authority_refs: string[];
}

export interface WorkBoardReorderColumnRequest {
  column_ref: string;
  card_refs: string[];
}

export interface WorkBoardReorderRequest {
  board_ref?: string;
  decision?: "approve";
  approval_ref?: string;
  exact_scope_ref?: string;
  action_envelope_ref?: string;
  decision_reason_ref: string;
  columns: WorkBoardReorderColumnRequest[];
  metadata_refs?: string[];
}

export interface WorkBoardReorderReceipt {
  receipt_ref: string;
  status: "applied" | "replayed";
  approval_ref: string;
  exact_scope_ref: string;
  action_envelope_ref: string;
  idempotency_ref: string;
  previous_order_ref: string;
  new_order_ref: string;
  proof_ref: string;
  evidence_ref: string;
  route_ref: string;
  safe_summary: string;
  replayed: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  connector_write_performed: boolean;
  provider_model_call_performed?: boolean;
  shell_subprocess_execution_performed: boolean;
  browser_automation_performed: boolean;
  background_autonomy_performed: boolean;
  production_authority_enabled: boolean;
}

export interface WorkBoardDragDropPostureReadModel {
  posture_ref: string;
  safe_summary: string;
  local_preview_enabled: boolean;
  keyboard_reorder_preview_enabled: boolean;
  durable_reorder_enabled: boolean;
  backend_mutation_route_available: boolean;
  receipt_created: boolean;
  rollback_available: boolean;
  mutation_route_ref: string;
  approval_required: boolean;
  exact_scope_required: boolean;
  idempotency_required: boolean;
  safe_disable_refs: string[];
  rollback_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
}

export interface WorkBoardReadModel {
  schema_version: "uaa-work-board-read-model.v1";
  contract_ref: string;
  board_ref: string;
  route_ref: string;
  backend_route_refs: string[];
  frontend_route_refs: string[];
  cli_inspection_refs: string[];
  docs_refs: string[];
  source_label: string;
  status: "backend_owned_read_model";
  title: string;
  safe_summary: string;
  northstar_ref: string;
  repo_safe_scope: string;
  full_strength_goal: string;
  columns: WorkBoardColumnReadModel[];
  cards: WorkBoardCardReadModel[];
  blocked_lanes: WorkBoardBlockedLaneReadModel[];
  drag_drop_posture: WorkBoardDragDropPostureReadModel;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  redactions_applied: string[];
  next_safe_action: string;
  backend_owned: boolean;
  read_only: boolean;
  safe_refs_only: boolean;
  non_authoritative_mock_fallback: boolean;
  raw_paths_included: boolean;
  raw_content_included: boolean;
  board_mutation_enabled: boolean;
  durable_drag_drop_enabled: boolean;
  durable_reorder_persistence_enabled: boolean;
  approval_required_for_reorder: boolean;
  reorder_route_ref: string;
  latest_reorder_receipt_ref: string | null;
  issue_tracker_write_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_automation_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
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

export type RunAttachedApprovalState =
  | "requested"
  | "approved"
  | "denied"
  | "expired"
  | "revoked"
  | "scope_mismatch_blocked"
  | "blocked";

export interface RunAttachedApprovalQueueItem {
  schema_version: "run_attached_approval_queue_item.v1";
  item_ref: string;
  approval_request_ref: string;
  approval_grant_ref?: string | null;
  run_ref: string;
  step_ref: string;
  requested_scope_ref: string;
  approval_state: RunAttachedApprovalState;
  approval_event_type: string;
  approval_decision_ref?: string | null;
  approval_receipt_ref?: string | null;
  approval_scope_validation_ref?: string | null;
  expiry_ref?: string | null;
  revocation_ref?: string | null;
  evidence_refs: string[];
  blocked_authority_refs: string[];
  receipt_refs: string[];
  audit_refs: string[];
  replay_refs: string[];
  rollback_refs: string[];
  idempotency_key_refs: string[];
  durable_attachment_status:
    | "attached"
    | "durable_attachment_missing"
    | "approval_state_missing";
  safe_summary: string;
  required_next_action: string;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  approval_refs_are_identifiers_only: boolean;
  approval_authority_enabled: boolean;
  execution_authority_enabled: boolean;
  ui_mutation_controls_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  model_call_enabled: boolean;
}

export interface RunAttachedApprovalRunBucket {
  run_ref: string;
  pending_approval_refs: string[];
  approval_history_refs: string[];
  latest_approval_state?: RunAttachedApprovalState | null;
  durable_attachment_statuses: string[];
  safe_refs_only: boolean;
}

export interface RunAttachedApprovalQueueSummary {
  schema_version: "run_attached_approval_queue_summary.v1";
  queue_ref: string;
  queue_item_count: number;
  run_count: number;
  pending_count: number;
  requested_count: number;
  approved_count: number;
  denied_count: number;
  expired_count: number;
  revoked_count: number;
  scope_mismatch_blocked_count: number;
  blocked_count: number;
  durable_attachment_missing_count: number;
  approval_grants_created: boolean;
  arbitrary_approval_ref_authority: boolean;
  safe_summary: string;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  approval_refs_are_identifiers_only: boolean;
  execution_authority_enabled: boolean;
  ui_mutation_controls_enabled: boolean;
}

export type UnifiedApprovalReviewSource =
  | "durable_run"
  | "provider_tool_contract"
  | "connector_delivery"
  | "coworker_handoff";

export interface UnifiedApprovalReviewItem {
  schema_version: "unified_approval_review_item.v1";
  item_ref: string;
  source_type: UnifiedApprovalReviewSource;
  title: string;
  approval_state: RunAttachedApprovalState;
  run_ref: string;
  source_ref: string;
  approval_ref?: string | null;
  approval_request_ref?: string | null;
  approval_decision_ref?: string | null;
  approval_receipt_ref?: string | null;
  requested_scope_ref: string;
  approval_scope_validation_ref?: string | null;
  expiry_ref?: string | null;
  revocation_ref?: string | null;
  provider_tool_contract_refs: string[];
  connector_delivery_refs: string[];
  coworker_handoff_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  audit_refs: string[];
  replay_refs: string[];
  rollback_refs: string[];
  blocked_authority_refs: string[];
  route_refs: string[];
  safe_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  approval_refs_are_identifiers_only: boolean;
  approval_ref_grants_authority: boolean;
  local_approval_authority_scope_validated: boolean;
  ui_mutation_controls_enabled: boolean;
  execution_authority_enabled: boolean;
  provider_model_calls_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  connector_sends_enabled: boolean;
  background_worker_enabled: boolean;
  scheduler_enabled: boolean;
}

export interface UnifiedApprovalReview {
  schema_version: "unified_approval_review.v1";
  source:
    | "python_core_unified_approval_review_read_model"
    | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  review_ref: string;
  route_ref: string;
  route_refs: string[];
  cli_ref: string;
  review_items: UnifiedApprovalReviewItem[];
  pending_approval_refs: string[];
  approval_history_refs: string[];
  run_refs: string[];
  provider_tool_contract_refs: string[];
  connector_delivery_refs: string[];
  coworker_handoff_refs: string[];
  proof_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  blocked_authority_refs: string[];
  pending_count: number;
  history_count: number;
  blocked_count: number;
  expired_count: number;
  revoked_count: number;
  scope_mismatch_blocked_count: number;
  safe_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  approval_refs_are_identifiers_only: boolean;
  approval_ref_grants_authority: boolean;
  ui_mutation_controls_enabled: boolean;
  execution_authority_enabled: boolean;
  provider_model_calls_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  connector_sends_enabled: boolean;
  background_worker_enabled: boolean;
  scheduler_enabled: boolean;
}

export type ConnectorDeliveryState =
  | "draft_created_metadata_only"
  | "pending_approval"
  | "approval_denied"
  | "delivery_blocked"
  | "delivery_ready_not_sent"
  | "retry_scheduled_metadata_only"
  | "failed_metadata_only"
  | "canceled_metadata_only"
  | "sent_not_supported";

export interface ConnectorDeliveryReviewQueueItem {
  schema_version: "connector_delivery_review_queue_item.v1";
  item_ref: string;
  delivery_ref: string;
  run_ref: string;
  connector_ref: string;
  channel_ref: string;
  target_session_ref: string;
  latest_state: ConnectorDeliveryState;
  delivery_state_label: string;
  delivery_execution_posture: string;
  event_refs: string[];
  redacted_subject_refs: string[];
  redacted_body_summary_refs: string[];
  outbound_approval_refs: string[];
  idempotency_key_refs: string[];
  blocked_reason_refs: string[];
  retry_refs: string[];
  failure_receipt_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  proof_refs: string[];
  audit_refs: string[];
  replay_refs: string[];
  rollback_refs: string[];
  safe_disable_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  no_send_action: boolean;
  metadata_only: boolean;
  raw_payloads_persisted: boolean;
  raw_body_persisted: boolean;
  raw_content_persisted: boolean;
  file_content_persisted: boolean;
  contact_data_persisted: boolean;
  credential_material_persisted: boolean;
  outbound_approval_refs_are_identifiers_only: boolean;
  target_session_ref_grants_authority: boolean;
  delivery_execution_performed: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  account_sync_enabled: boolean;
  oauth_enabled: boolean;
  credential_collection_enabled: boolean;
  provider_model_calls_enabled: boolean;
  live_web_runtime_enabled: boolean;
  browser_runtime_enabled: boolean;
  shell_runtime_enabled: boolean;
  background_delivery_worker_enabled: boolean;
  scheduler_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ConnectorDeliveryReviewQueue {
  schema_version: "connector_delivery_review_queue.v1";
  source:
    | "python_core_connector_delivery_review_queue_read_model"
    | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  review_ref: string;
  route_ref: string;
  route_refs: string[];
  cli_ref: string;
  queue_items: ConnectorDeliveryReviewQueueItem[];
  delivery_refs: string[];
  run_refs: string[];
  connector_refs: string[];
  channel_refs: string[];
  target_session_refs: string[];
  outbound_approval_refs: string[];
  idempotency_key_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  proof_refs: string[];
  blocked_reason_refs: string[];
  blocked_authority_refs: string[];
  state_counts: Record<string, number>;
  delivery_count: number;
  pending_count: number;
  delivery_ready_not_sent_count: number;
  blocked_count: number;
  retry_count: number;
  failure_count: number;
  safe_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  no_send_action: boolean;
  metadata_only: boolean;
  outbound_approval_refs_are_identifiers_only: boolean;
  target_session_refs_grant_authority: boolean;
  delivery_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  connector_sends_enabled: boolean;
  account_sync_enabled: boolean;
  oauth_enabled: boolean;
  credential_collection_enabled: boolean;
  provider_model_calls_enabled: boolean;
  live_web_runtime_enabled: boolean;
  browser_runtime_enabled: boolean;
  shell_runtime_enabled: boolean;
  background_delivery_worker_enabled: boolean;
  scheduler_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface RunAttachedApprovalQueue {
  schema_version: "run_attached_approval_queue.v1";
  source:
    | "python_core_run_attached_approval_queue_read_model"
    | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  queue_ref: string;
  route_ref: string;
  route_refs: string[];
  cli_ref: string;
  supported_approval_states: RunAttachedApprovalState[];
  supported_approval_event_types: string[];
  queue_items: RunAttachedApprovalQueueItem[];
  pending_approvals_by_run: RunAttachedApprovalRunBucket[];
  approval_history_by_run: RunAttachedApprovalRunBucket[];
  summary: RunAttachedApprovalQueueSummary;
  unified_review: UnifiedApprovalReview;
  connector_delivery_review_queue?: ConnectorDeliveryReviewQueue;
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  approval_refs_are_identifiers_only: boolean;
  approval_authority_enabled: boolean;
  execution_authority_enabled: boolean;
  ui_mutation_controls_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  model_call_enabled: boolean;
}

export type RunObservabilityStatus =
  | "implemented_read_only"
  | "state_not_found_no_write";

export interface RunOrchestrationCheckpointSummary {
  checkpoint_ref: string;
  checkpoint_status: string;
  sequence: number;
  safe_summary: string;
  evidence_refs: string[];
  receipt_refs: string[];
  rollback_refs: string[];
  replay_refs: string[];
  safe_refs_only: boolean;
  raw_payloads_persisted: boolean;
  execution_performed: boolean;
}

export interface RunRetryRecoveryPosture {
  retry_state: string;
  recovery_state: string;
  retry_refs: string[];
  recovery_refs: string[];
  idempotency_key_refs: string[];
  retry_execution_enabled: boolean;
  recovery_execution_enabled: boolean;
  next_safe_action: string;
}

export interface RunApprovalWaitState {
  wait_state: string;
  pending_approval_refs: string[];
  approval_history_refs: string[];
  pending_count: number;
  approval_refs_are_identifiers_only: boolean;
  approval_ref_grants_authority: boolean;
  exact_scope_required_before_mutation: boolean;
  resume_execution_enabled: boolean;
}

export interface RunCancellationDeadLetterState {
  cancellation_state: string;
  dead_letter_state: string;
  cancellation_refs: string[];
  dead_letter_refs: string[];
  cancel_execution_enabled: boolean;
  dead_letter_execution_enabled: boolean;
  next_safe_action: string;
}

export interface RunRedactedErrorSummary {
  error_ref: string;
  safe_summary: string;
  evidence_refs: string[];
  raw_error_omitted: boolean;
}

export interface RunObservabilityReadModel {
  schema_version: "run_observability_read_model.v1";
  contract_ref: string;
  source:
    | "python_core_run_observability_read_model"
    | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  status: RunObservabilityStatus;
  run_ref: string;
  selected_run_ref?: string | null;
  route_ref: string;
  route_refs: string[];
  cli_ref: string;
  lifecycle?: Record<string, unknown> | null;
  progress?: Record<string, unknown> | null;
  current_phase_ref: string;
  current_phase_status: string;
  current_step_ref: string;
  current_step_status: string;
  checkpoint_summaries: RunOrchestrationCheckpointSummary[];
  retry_recovery_posture: RunRetryRecoveryPosture;
  approval_wait_state: RunApprovalWaitState;
  cancellation_dead_letter_state: RunCancellationDeadLetterState;
  redacted_error_summaries: RunRedactedErrorSummary[];
  approval_queue: RunAttachedApprovalQueue;
  coworker_workers: Record<string, unknown>;
  connector_deliveries: Record<string, unknown>;
  connector_delivery_review_queue: ConnectorDeliveryReviewQueue;
  run_refs: string[];
  lifecycle_event_refs: string[];
  progress_event_refs: string[];
  approval_refs: string[];
  coworker_handoff_refs: string[];
  connector_delivery_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  event_count: number;
  progress_event_count: number;
  approval_item_count: number;
  coworker_event_count: number;
  connector_delivery_count: number;
  connector_delivery_review_count: number;
  safe_summary: string;
  next_safe_action: string;
  cancel_control_status: string;
  resume_control_status: string;
  streaming_status: string;
  background_worker_status: string;
  provider_model_status: string;
  tool_execution_status: string;
  connector_execution_status: string;
  autonomous_execution_status: string;
  proof_detail_status: string;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  raw_payloads_persisted: boolean;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_payload_content_stored: boolean;
  approval_refs_are_identifiers_only: boolean;
  approval_ref_grants_authority: boolean;
  control_center_presentation_only: boolean;
  ui_mutation_controls_enabled: boolean;
  cancel_resume_controls_enabled: boolean;
  live_streaming_runtime_enabled: boolean;
  provider_model_calls_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_writes_enabled: boolean;
  connector_sends_enabled: boolean;
  background_worker_enabled: boolean;
  scheduler_enabled: boolean;
  autonomous_execution_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ApiSummary {
  route_count: number;
  control_center_route_count: number;
  operation_ids_unique: boolean;
  execution_routes_present: boolean;
}

export interface FounderLoopActionApprovalEnvelope {
  schema_version: "founder_loop_action_approval_envelope.v1";
  contract_ref: string;
  source:
    "python_core_action_inbox_read_model" | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  action_kind: string;
  exact_scope: string;
  risk_class: string;
  side_effect_class: string;
  approval_requirement: string;
  expiry_or_staleness: string;
  idempotency_ref: string;
  expected_receipt_refs: string[];
  rollback_safe_disable_posture: string;
  estimated_cost_usd: number;
  max_approved_cost_usd: number;
  provider_ref: string;
  model_profile_ref: string;
  input_metered_units: number;
  output_metered_units: number;
  total_metered_units: number;
  cost_estimate_ref: string;
  captured_usage_ref: string;
  budget_decision_ref: string;
  cost_receipt_refs: string[];
  cost_blocked_state_refs?: string[];
  cost_state_label: string;
  provider_authority_state_label: string;
  unknown_paid_cost_requires_explicit_approval: boolean;
  frontier_usage_claimed: boolean;
  blocked_authority_refs: string[];
  evidence_refs: string[];
  missing_field_states: string[];
}

export interface FounderLoopActionReceiptVisibility {
  schema_version: "founder_loop_action_receipt_visibility.v1";
  contract_ref: string;
  source:
    "python_core_action_inbox_read_model" | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  decision_receipt_ref: string;
  local_task_ref: string;
  local_task_commit_receipt_ref: string;
  evidence_timeline_event_ref: string;
  replay_posture: string;
  conflict_posture: string;
  missing_field_states: string[];
}

export type FounderLoopWorkClassificationValue =
  | "judgment_required"
  | "mechanical"
  | "validation"
  | "bookkeeping"
  | "ambiguous"
  | "blocked";

export interface FounderLoopWorkClassification {
  schema_version: "fcc_fusion_work_classification.v1";
  contract_ref: string;
  classification: FounderLoopWorkClassificationValue;
  reason_refs: string[];
  confidence_posture: string;
  ambiguity_posture: string;
  human_review_required: boolean;
  blocked_authority_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  reviewed_at_ref: string;
  expiry_posture_ref: string;
  review_aid_only: boolean;
  execution_authorized: boolean;
  action_execution_enabled: boolean;
}

export interface FounderLoopRouteDecisionVisibility {
  schema_version: "fcc_fusion_route_decision_visibility.v1";
  contract_ref: string;
  status: "selected" | "rejected" | "blocked";
  selected_profile_ref: string;
  rejected_profile_refs: string[];
  reason_codes: string[];
  privacy_posture_ref: string;
  cost_posture_ref: string;
  latency_posture_ref: string;
  context_posture_ref: string;
  approval_posture_ref: string;
  operator_summary: string;
  no_execution_performed: boolean;
  model_invocation_performed: boolean;
  provider_call_performed: boolean;
}

export interface FounderLoopCacheContextEconomics {
  schema_version: "fcc_fusion_cache_context_economics.v1";
  contract_ref: string;
  context_budget_ref: string;
  compaction_boundary_ref: string;
  cache_miss_expected: boolean;
  cache_reuse_posture: string;
  reroute_reason: string;
  estimated_context_cost_posture: string;
  cache_or_context_blocker_refs: string[];
  evidence_refs: string[];
  explanatory_posture_only: boolean;
  measured_provider_event: boolean;
  runtime_model_switch_performed: boolean;
}

export interface FounderLoopDelegationProposal {
  schema_version: "fcc_fusion_delegation_proposal.v1";
  contract_ref: string;
  proposal_state: "proposed" | "rejected" | "deferred" | "blocked" | "future_only";
  proposed_delegate_kind: string;
  delegate_scope_ref: string;
  main_owner_responsibility_refs: string[];
  delegated_work_refs: string[];
  review_required_posture_ref: string;
  blocked_execution_refs: string[];
  expected_receipt_refs: string[];
  rollback_safe_disable_posture_refs: string[];
  work_classification: FounderLoopWorkClassification;
  future_only: boolean;
  creates_approval_ref: boolean;
  creates_execution_ref: boolean;
  worker_execution_enabled: boolean;
  background_dispatch_enabled: boolean;
}

export interface FounderLoopFusionDogfoodEvidenceRecord {
  schema_version: "fcc_fusion_dogfood_evidence.v1";
  contract_ref: string;
  review_record_ref: string;
  outcome: string;
  friction_delta_ref: string;
  review_time_delta_ref: string;
  cost_confusion_delta_ref: string;
  routing_cost_delta_ref: string;
  ambiguity_delta_ref: string;
  interruption_delta_ref: string;
  redacted_summary_ref: string;
  evidence_refs: string[];
  local_private_only: boolean;
  external_analytics_enabled: boolean;
  live_learning_claimed: boolean;
}

export interface FounderLoopFusionRoutingDelegationReadModel {
  schema_version: "fcc_fusion_routing_delegation.v1";
  contract_ref: string;
  source: string;
  status: string;
  backend_owned: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  surfaces: string[];
  work_classifications: FounderLoopWorkClassification[];
  route_decisions: FounderLoopRouteDecisionVisibility[];
  delegation_proposals: FounderLoopDelegationProposal[];
  cache_context_economics: FounderLoopCacheContextEconomics[];
  dogfood_records: FounderLoopFusionDogfoodEvidenceRecord[];
  blocked_state_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  action_execution_enabled: boolean;
  sidekick_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  connector_write_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  background_dispatch_enabled: boolean;
  production_authority_enabled: boolean;
}

export type CrmM1ImplementationState =
  | "fixture_only"
  | "read_only"
  | "proposal_only"
  | "blocked";

export type CrmM1WorkspaceKind =
  | "real_estate"
  | "finance_insurance"
  | "healthcare"
  | "retail_ecommerce"
  | "professional_services";

export interface CrmM1FixtureLane {
  lane_ref: string;
  safe_label: string;
  state: "fixture_only";
  item_refs: string[];
  evidence_refs: string[];
}

export interface CrmM1FixtureSection {
  section_ref: string;
  section_kind:
    | "pipeline"
    | "relationship_inspector"
    | "work_queue"
    | "communications_metadata"
    | "evidence"
    | "memory_provenance"
    | "blocked_authority"
    | "vertical_context";
  safe_label: string;
  state: CrmM1ImplementationState;
  evidence_refs: string[];
  blocked_authority_refs: string[];
}

export interface CrmM1VerticalFixture {
  workspace_kind: CrmM1WorkspaceKind;
  source_m0_contract_ref: string;
  source_preset_pack_ref: string;
  safe_display_label: string;
  state: "fixture_only";
  nav_refs: string[];
  object_kind_refs: string[];
  work_queue_refs: string[];
  pipeline_refs: string[];
  inspector_section_refs: string[];
  state_labels: CrmM1ImplementationState[];
  pipeline_lanes: CrmM1FixtureLane[];
  screen_sections: CrmM1FixtureSection[];
  communications_metadata_refs: string[];
  evidence_refs: string[];
  memory_provenance_refs: string[];
  next_safe_action_refs: string[];
  blocked_authority_refs: string[];
  fixture_only: boolean;
  backend_read_model_added: boolean;
  backend_route_added: boolean;
  control_center_route_added: boolean;
  control_center_route_ref: string;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  send_enabled: boolean;
  calendar_write_enabled: boolean;
  contact_import_enabled: boolean;
  silent_identity_merge_enabled: boolean;
  provider_model_call_enabled: boolean;
  live_web_enabled: boolean;
  browser_runtime_enabled: boolean;
  hidden_context_injection_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface CrmM1FixtureShell {
  contract_ref: string;
  docs_refs: string[];
  source_m0_contract_ref: string;
  source: "python_core_crm_m1_fixture_contract";
  state: "fixture_only";
  state_labels: CrmM1ImplementationState[];
  verticals: CrmM1VerticalFixture[];
  blocked_authority_refs: string[];
  prompts_executed_refs: string[];
  fixture_only: boolean;
  backend_read_model_added: boolean;
  backend_route_added: boolean;
  control_center_route_added: boolean;
  control_center_route_ref: string;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  send_enabled: boolean;
  calendar_write_enabled: boolean;
  contact_import_enabled: boolean;
  silent_identity_merge_enabled: boolean;
  provider_model_call_enabled: boolean;
  live_web_enabled: boolean;
  browser_runtime_enabled: boolean;
  hidden_context_injection_enabled: boolean;
  public_beta_claimed: boolean;
  production_authority_enabled: boolean;
}

export interface CrmAuthorityPostureReadModel {
  posture_ref: string;
  backend_owned: boolean;
  control_center_grants_authority: boolean;
  read_only_routes_enabled: boolean;
  exact_local_mutation_lane_enabled: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  send_enabled: boolean;
  calendar_write_enabled: boolean;
  provider_model_call_enabled: boolean;
  live_web_enabled: boolean;
  browser_runtime_enabled: boolean;
  background_autonomy_enabled: boolean;
  external_crm_write_enabled: boolean;
  production_authority_enabled: boolean;
  blocked_authority_refs: string[];
}

export interface CrmStorageStatusReadModel {
  storage_ref: string;
  state: "code_seed" | "seeded_demo" | "local_state" | "cleared_demo";
  initialized: boolean;
  seeded_demo: boolean;
  record_counts: Record<string, number>;
  event_log_ref: string;
  snapshot_ref: string;
  raw_paths_omitted: boolean;
  raw_contact_details_omitted: boolean;
  connector_sync_enabled: boolean;
  account_sync_enabled: boolean;
}

export interface CrmPersonReadModel {
  person_ref: string;
  safe_display_label: string;
  relationship_refs: string[];
  organization_refs: string[];
  evidence_refs: string[];
  memory_provenance_refs: string[];
  tags: string[];
  raw_contact_details_included: boolean;
  account_sync_enabled: boolean;
}

export interface CrmOrganizationReadModel {
  organization_ref: string;
  safe_display_label: string;
  relationship_refs: string[];
  evidence_refs: string[];
  raw_contact_details_included: boolean;
  account_sync_enabled: boolean;
}

export interface CrmRelationshipReadModel {
  relationship_ref: string;
  person_ref: string;
  organization_ref?: string | null;
  safe_display_label: string;
  relationship_kind_ref: string;
  health_state: "warm" | "steady" | "stale" | "blocked" | "needs_evidence";
  safe_summary: string;
  why_shown: string;
  timeline_event_refs: string[];
  follow_up_refs: string[];
  opportunity_refs: string[];
  evidence_refs: string[];
  memory_provenance_refs: string[];
  stale_state: "fresh" | "stale" | "conflict" | "missing_evidence";
  raw_contact_details_included: boolean;
}

export interface CrmTimelineEventReadModel {
  event_ref: string;
  relationship_ref: string;
  event_kind: string;
  occurred_at_ref: string;
  safe_summary: string;
  why_shown: string;
  source_refs: string[];
  evidence_refs: string[];
  memory_provenance_refs: string[];
  proof_refs: string[];
  stale_conflict_posture: "fresh" | "stale" | "conflict" | "missing_evidence";
  raw_content_included: boolean;
}

export interface CrmFollowUpReadModel {
  follow_up_ref: string;
  relationship_ref: string;
  status: "due" | "upcoming" | "stale" | "blocked" | "proposed" | "completed";
  priority: "high" | "medium" | "low";
  due_ref: string;
  safe_summary: string;
  reason_refs: string[];
  evidence_refs: string[];
  memory_provenance_refs: string[];
  opportunity_refs: string[];
  action_inbox_handoff_proposal_ref: string;
  action_inbox_handoff_proposal_only: boolean;
  send_enabled: boolean;
  calendar_write_enabled: boolean;
  connector_write_enabled: boolean;
}

export interface CrmOpportunityReadModel {
  opportunity_ref: string;
  relationship_ref: string;
  pipeline_ref: string;
  opportunity_kind: string;
  stage_ref: string;
  stage_label: string;
  safe_summary: string;
  evidence_refs: string[];
  proof_refs: string[];
  local_preview_drag_drop_enabled: boolean;
  persisted_stage_mutation_route_ref: string;
  external_crm_write_enabled: boolean;
  fake_revenue_claim_enabled: boolean;
}

export interface CrmPipelineStageReadModel {
  stage_ref: string;
  safe_label: string;
  opportunity_refs: string[];
}

export interface CrmPipelineReadModel {
  pipeline_ref: string;
  safe_label: string;
  stages: CrmPipelineStageReadModel[];
  opportunity_refs: string[];
  evidence_refs: string[];
  local_preview_drag_drop_enabled: boolean;
  persisted_reorder_requires_exact_mutation: boolean;
  external_sync_enabled: boolean;
}

export interface CrmSmartListReadModel {
  smart_list_ref: string;
  safe_label: string;
  membership_rule_ref: string;
  explanation: string;
  relationship_refs: string[];
  follow_up_refs: string[];
  opportunity_refs: string[];
  evidence_refs: string[];
  hidden_context_injection_enabled: boolean;
  external_sync_enabled: boolean;
}

export interface CrmCommunicationDraftReadModel {
  draft_ref: string;
  relationship_ref: string;
  draft_kind: string;
  bounded_redacted_summary: string;
  proof_refs: string[];
  local_review_artifact_only: boolean;
  send_enabled: boolean;
  calendar_write_enabled: boolean;
  connector_write_enabled: boolean;
  raw_body_persisted: boolean;
}

export interface CrmAiProposalReadModel {
  proposal_ref: string;
  proposal_type: string;
  relationship_ref: string;
  safe_summary: string;
  proof_refs: string[];
  deterministic_fixture: boolean;
  proposal_only: boolean;
  provider_model_call_enabled: boolean;
  model_output_authority_enabled: boolean;
  raw_prompt_or_response_persisted: boolean;
}

export interface CrmReportReadModel {
  report_ref: string;
  safe_label: string;
  value_label: string;
  freshness_ref: string;
  drilldown_refs: string[];
  evidence_refs: string[];
  fake_revenue_claim_enabled: boolean;
  external_sync_claim_enabled: boolean;
}

export interface CrmConnectorReadLaneReadModel {
  posture_ref: string;
  lanes: Array<Record<string, string>>;
  readiness_status: string;
  source_scope_ref: string;
  test_account_scope_ref: string;
  gateway_boundary_ref: string;
  policy_decision_ref: string;
  approval_scope_ref: string;
  audit_schema_ref: string;
  redaction_policy_ref: string;
  safe_disable_ref: string;
  rollback_readiness_ref: string;
  proof_ref: string;
  evidence_ref: string;
  cli_inspection_ref: string;
  api_surface_ref: string;
  control_center_surface_ref: string;
  blocker_report_refs: string[];
  missing_prerequisite_refs: string[];
  promotion_path_refs: string[];
  disabled_by_default: boolean;
  unblock_prompt_ref: string;
  connector_runtime_enabled: boolean;
  connector_writes_enabled: boolean;
  raw_body_ingestion_enabled: boolean;
  live_connector_read_performed: boolean;
  external_account_auth_enabled: boolean;
  background_polling_enabled: boolean;
  provider_model_call_enabled: boolean;
}

export interface CrmSendsWritesAuthorityPlanReadModel {
  plan_ref: string;
  lane_refs: string[];
  blocker_report_refs: string[];
  unblock_prompt_refs: string[];
  sends_enabled: boolean;
  connector_writes_enabled: boolean;
  calendar_writes_enabled: boolean;
  external_crm_writes_enabled: boolean;
}

export interface CrmImportExportPostureReadModel {
  contract_ref: string;
  import_preview_cli_ref: string;
  export_redacted_cli_ref: string;
  exact_import_commit_enabled: boolean;
  export_redacted_snapshot_enabled: boolean;
  no_raw_path_persistence: boolean;
  identity_match_review_only: boolean;
  silent_merge_enabled: boolean;
}

export interface CrmLocalCommandCenterReadModel {
  schema_version: string;
  contract_ref: string;
  source_m0_contract_ref: string;
  source: string;
  state: "fixture_only" | "read_only" | "proposal_only" | "blocked";
  backend_owned: boolean;
  read_only: boolean;
  safe_refs_only: boolean;
  route_refs: string[];
  cli_refs: string[];
  redactions_applied: string[];
  authority_posture: CrmAuthorityPostureReadModel;
  storage_status: CrmStorageStatusReadModel;
  people: CrmPersonReadModel[];
  organizations: CrmOrganizationReadModel[];
  relationships: CrmRelationshipReadModel[];
  timeline_events: CrmTimelineEventReadModel[];
  follow_ups: CrmFollowUpReadModel[];
  opportunities: CrmOpportunityReadModel[];
  pipelines: CrmPipelineReadModel[];
  smart_lists: CrmSmartListReadModel[];
  communication_drafts: CrmCommunicationDraftReadModel[];
  ai_proposals: CrmAiProposalReadModel[];
  reports: CrmReportReadModel[];
  connector_read_lanes: CrmConnectorReadLaneReadModel;
  sends_writes_authority_plan: CrmSendsWritesAuthorityPlanReadModel;
  import_export_posture: CrmImportExportPostureReadModel;
  blocked_authority_refs: string[];
  raw_contact_details_included: boolean;
  raw_message_bodies_included: boolean;
  raw_paths_included: boolean;
  provider_payloads_included: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopTaskDecompositionStep {
  step_ref: string;
  title: string;
  safe_summary: string;
  depends_on: string[];
  dependency_refs: string[];
  evidence_refs: string[];
  ambiguity_refs: string[];
  missing_evidence_refs: string[];
  suggested_action_inbox_proposal_ref?: string | null;
  required_approval_refs: string[];
  blocked_authority_refs: string[];
  risk_class: string;
  why_proposed: string;
  what_this_affects: string[];
  review_only: boolean;
  proposal_only: boolean;
  execution_performed: boolean;
  safe_refs_only: boolean;
}

export interface FounderLoopTaskDecompositionRisk {
  risk_ref: string;
  risk_class: string;
  safe_summary: string;
  mitigation_ref: string;
  blocked_authority_ref: string;
  evidence_refs: string[];
}

export interface FounderLoopTaskDecompositionAuthorityPosture {
  review_only: boolean;
  proposal_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  local_task_commit_eligible: boolean;
  action_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_network_enabled: boolean;
  model_provider_authority_allowed: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopTaskDecompositionProposalSummary {
  contract_ref: string;
  source: string;
  status: string;
  proposal_count: number;
  action_kind: string;
  proposal_refs: string[];
  action_item_refs: string[];
  blocked_authority_refs: string[];
  review_only: boolean;
  proposal_only: boolean;
  local_task_commit_eligible: boolean;
  action_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_network_enabled: boolean;
  model_provider_authority_allowed: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopLocalTaskSafeDisablePosture {
  schema_version: "founder_loop_local_task_safe_disable_posture.v1";
  source: string;
  backend_owned: boolean;
  lane_id: string;
  action_kind: "local_task_create";
  local_task_commits_enabled: boolean;
  safe_disable_active: boolean;
  safe_disable_ref: string;
  rollback_ref: string;
  safe_disable_posture_ref: string;
  disabled_reason_refs: string[];
  blocked_state_refs: string[];
  rollback_execution_enabled: boolean;
  rollback_blocker_refs: string[];
  next_safe_action: string;
  updated_at?: string;
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
  action_envelope_contract_ref?: string;
  action_envelope_ref?: string;
  action_envelope_status?: string;
  action_envelope_safe_summary?: string;
  action_scope_ref?: string;
  action_approval_requirement_ref?: string;
  action_review_actions?: string[];
  action_review_posture_refs?: string[];
  action_expected_receipt_refs?: string[];
  action_idempotency_key_ref?: string;
  action_expires_at?: string;
  action_stale_state?: string;
  action_rollback_ref?: string;
  action_safe_disable_ref?: string;
  action_blocked_state_refs?: string[];
  action_authority_boundary?: string;
  action_exact_scope_required?: boolean;
  action_envelope_approval_ref_authority?: boolean;
  action_envelope_grant_capture_enabled?: boolean;
  action_envelope_execution_enabled?: boolean;
  action_envelope_tool_execution_enabled?: boolean;
  action_envelope_workflow_execution_enabled?: boolean;
  action_envelope_browser_execution_enabled?: boolean;
  action_envelope_connector_runtime_enabled?: boolean;
  action_envelope_connector_write_enabled?: boolean;
  action_envelope_shell_execution_enabled?: boolean;
  action_envelope_model_provider_authority_allowed?: boolean;
  action_envelope_safe_refs_only?: boolean;
  action_envelope_raw_content_included?: boolean;
  action_envelope_cost_contract_ref?: string;
  action_envelope_estimated_cost_usd?: number;
  action_envelope_max_approved_cost_usd?: number;
  action_envelope_provider_ref?: string;
  action_envelope_model_profile_ref?: string;
  action_envelope_input_metered_units?: number;
  action_envelope_output_metered_units?: number;
  action_envelope_total_metered_units?: number;
  action_envelope_cost_estimate_ref?: string;
  action_envelope_captured_usage_ref?: string;
  action_envelope_budget_decision_ref?: string;
  action_envelope_cost_receipt_refs?: string[];
  action_envelope_cost_blocked_state_refs?: string[];
  action_envelope_cost_state_label?: string;
  action_envelope_provider_authority_state_label?: string;
  action_envelope_unknown_paid_cost_requires_explicit_approval?: boolean;
  action_envelope_frontier_usage_claimed?: boolean;
  estimated_cost_usd?: number;
  max_approved_cost_usd?: number;
  provider_ref?: string;
  model_profile_ref?: string;
  input_metered_units?: number;
  output_metered_units?: number;
  total_metered_units?: number;
  cost_estimate_ref?: string;
  captured_usage_ref?: string;
  budget_decision_ref?: string;
  cost_receipt_refs?: string[];
  cost_blocked_state_refs?: string[];
  cost_state_label?: string;
  provider_authority_state_label?: string;
  unknown_paid_cost_requires_explicit_approval?: boolean;
  frontier_usage_claimed?: boolean;
  action_kind?: string;
  local_task_commit_contract_ref?: string;
  local_task_commit_route_ref?: string;
  local_task_ref?: string | null;
  local_task_commit_approval_ref?: string | null;
  local_task_commit_approval_status?: string;
  local_task_commit_eligible?: boolean;
  local_task_commit_receipt_ref?: string | null;
  local_task_commit_blocked_reasons?: string[];
  local_task_commit_next_safe_action?: string;
  local_task_commit_external_authority_blocked_refs?: string[];
  local_task_safe_disable_posture?: FounderLoopLocalTaskSafeDisablePosture;
  local_task_safe_disable_ref?: string;
  local_task_safe_disable_active?: boolean;
  local_task_safe_disable_posture_ref?: string;
  local_task_rollback_ref?: string;
  local_task_rollback_execution_enabled?: boolean;
  local_task_rollback_blocker_refs?: string[];
  action_group_id?: FounderLoopActionGroupId;
  action_group_label?: string;
  action_group_reason?: string;
  action_group_available_action?: string;
  approval_envelope?: FounderLoopActionApprovalEnvelope;
  receipt_visibility?: FounderLoopActionReceiptVisibility;
  work_classification?: FounderLoopWorkClassification;
  delegation_proposal?: FounderLoopDelegationProposal;
  cache_context_economics?: FounderLoopCacheContextEconomics;
  source_readiness_proposal_ref?: string;
  source_readiness_proposal_kind?: string;
  source_readiness_missing_contract_ref?: string;
  source_readiness_ref?: string;
  source_readiness_route_ref?: string;
  source_readiness_blocked_authority_refs?: string[];
  source_readiness_backend_owned?: boolean;
  source_readiness_proposal_classification?: "proposal_only_no_execution_path";
  health_recommendation_ref?: string;
  health_recommendation_kind?: string;
  health_recommendation_severity?: string;
  health_recommendation_lifecycle_state?: string;
  health_recommendation_missing_proof_refs?: string[];
  health_recommendation_validation_plan_refs?: string[];
  health_recommendation_expected_receipt_refs?: string[];
  health_recommendation_conversion_option_refs?: string[];
  health_recommendation_blocked_authority_refs?: string[];
  health_recommendation_auto_apply_authorized?: boolean;
  health_recommendation_auto_code_authorized?: boolean;
  health_recommendation_provider_model_call_authorized?: boolean;
  health_recommendation_shell_execution_authorized?: boolean;
  health_recommendation_connector_write_authorized?: boolean;
  health_recommendation_memory_write_authorized?: boolean;
  health_recommendation_context_injection_authorized?: boolean;
  health_recommendation_action_execution_authorized?: boolean;
  health_recommendation_production_authority_enabled?: boolean;
  health_recommendation_source_signal_refs?: string[];
  health_recommendation_source_route_refs?: string[];
  health_recommendation_rollback_or_safe_disable_refs?: string[];
  task_decomposition_proposal_ref?: string;
  task_decomposition_review_envelope_ref?: string;
  task_decomposition_plans_bridge_ref?: string;
  task_decomposition_action_inbox_bridge_ref?: string;
  task_decomposition_step_refs?: string[];
  task_decomposition_dependency_refs?: string[];
  task_decomposition_ambiguity_refs?: string[];
  task_decomposition_missing_evidence_refs?: string[];
  task_decomposition_required_approvals?: string[];
  task_decomposition_blocked_authority_refs?: string[];
  task_decomposition_why_proposed?: string;
  task_decomposition_what_this_affects?: string[];
  task_decomposition_review_only?: boolean;
  task_decomposition_proposal_only?: boolean;
  task_decomposition_execution_performed?: boolean;
  task_decomposition_runtime_authority_granted?: boolean;
  task_decomposition_execution_authorized?: boolean;
  task_decomposition_action_execution_enabled?: boolean;
  task_decomposition_tool_execution_enabled?: boolean;
  task_decomposition_workflow_execution_enabled?: boolean;
  task_decomposition_memory_write_authorized?: boolean;
  task_decomposition_context_injection_authorized?: boolean;
  task_decomposition_connector_write_enabled?: boolean;
  task_decomposition_shell_subprocess_execution_enabled?: boolean;
  task_decomposition_browser_network_enabled?: boolean;
  task_decomposition_model_provider_authority_allowed?: boolean;
  task_decomposition_public_beta_claim_enabled?: boolean;
  task_decomposition_production_authority_enabled?: boolean;
  created_at?: string;
  updated_at?: string;
}

export type FounderLoopActionGroupId =
  | "ready_for_decision"
  | "approved_local_task_lane"
  | "blocked_by_authority"
  | "expired_stale"
  | "receipt_recorded"
  | "proposal_only_no_execution_path";

export interface FounderLoopActionGroupSummary {
  group_id: FounderLoopActionGroupId;
  label: string;
  safe_summary: string;
  available_action: string;
  count: number;
}

export interface FounderLoopActionInboxWorkQueueLane {
  lane_id: FounderLoopActionGroupId;
  lane_ref: string;
  label: string;
  status: string;
  safe_summary: string;
  available_action: string;
  count: number;
  item_refs: string[];
  tier: string;
  blocked_authority_refs: string[];
}

export interface FounderLoopActionInboxWorkQueueNextItem {
  item_ref: string;
  title: string;
  lane_id: FounderLoopActionGroupId;
  lane_label: string;
  status: string;
  priority: string;
  risk_class: string;
  action_kind: string;
  available_action: string;
  next_safe_action: string;
  approval_required: boolean;
  approval_envelope_ref?: string | null;
  expected_receipt_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  proof_ref: string;
  local_task_commit_eligible: boolean;
  local_task_commit_route_ref?: string | null;
  rollback_ref?: string | null;
  safe_disable_ref?: string | null;
  blocked_authority_refs: string[];
}

export interface FounderLoopActionInboxWorkQueueWorkItem {
  item_ref: string;
  title: string;
  lane_id: FounderLoopActionGroupId;
  lane_label: string;
  status: string;
  priority: string;
  risk_class: string;
  action_kind: string;
  side_effect_class: string;
  safe_summary: string;
  approval_posture: string;
  receipt_posture: string;
  mutation_control_posture: string;
  next_safe_action: string;
  approval_required: boolean;
  operator_actionable: boolean;
  local_task_commit_eligible: boolean;
  fake_mutation_control_exposed: boolean;
  approval_envelope_ref?: string | null;
  local_task_commit_route_ref?: string | null;
  proof_ref: string;
  expected_receipt_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  rollback_ref?: string | null;
  safe_disable_ref?: string | null;
  blocked_authority_refs: string[];
}

export interface FounderLoopActionInboxWorkQueueReadModel {
  schema_version: "action-inbox-work-queue.v1";
  contract_ref: string;
  source:
    | "python_core_action_inbox_work_queue_read_model"
    | "mock_fallback_non_authoritative";
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  queue_ref: string;
  route_ref: string;
  cli_ref: string;
  proof_route_ref: string;
  item_count: number;
  operator_actionable_count: number;
  ready_for_decision_count: number;
  approved_local_task_count: number;
  proposal_only_count: number;
  blocked_count: number;
  receipt_recorded_count: number;
  lane_count: number;
  lanes: FounderLoopActionInboxWorkQueueLane[];
  work_item_count: number;
  work_item_refs: string[];
  work_items: FounderLoopActionInboxWorkQueueWorkItem[];
  next_item?: FounderLoopActionInboxWorkQueueNextItem | null;
  next_item_ref?: string | null;
  next_safe_action: string;
  operator_summary: string;
  tier_posture: string;
  mutating_controls_posture: string;
  tier_3_exact_local_task_commit_available: boolean;
  fake_mutation_controls_exposed: boolean;
  unsafe_ref_omitted_count: number;
  unsafe_ref_blocked_state_refs: string[];
  blocked_authority_refs: string[];
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_authorized: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopRuntimeActionInboxBridgeItem {
  invocation_ref: string;
  action_envelope_ref: string;
  adapter_id: string;
  requested_authority: string;
  command_intent?: string | null;
  status: string;
  approval_validated: boolean;
  execution_performed: boolean;
  exact_scope_ref: string;
  approval_ref: string;
  approval_decision_ref?: string | null;
  approval_validation_ref?: string | null;
  idempotency_ref: string;
  policy_decision_ref: string;
  payload_fingerprint_ref: string;
  rollback_ref: string;
  safe_disable_ref: string;
  safe_disable_posture_ref: string;
  receipt_ref?: string | null;
  execution_result_ref?: string | null;
  signed_evidence_ref?: string | null;
  signed_evidence_verifier_ref?: string | null;
  signed_evidence_verification_status: string;
  receipt_status: string;
  exit_code?: number | null;
  timed_out: boolean;
  command_output_persisted: boolean;
  receipt_refs: string[];
  evidence_refs: string[];
  blocked_reason_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
}

export interface FounderLoopRuntimeActionInboxBridgeReadModel {
  schema_version: "governed-runtime-action-inbox-bridge.v1";
  contract_ref: string;
  source: "python_core_runtime_gateway_action_inbox_bridge_read_model";
  backend_owned: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  route_ref: string;
  cli_ref: string;
  runtime_parity_loop_api_ref: string;
  runtime_parity_loop_cli_ref: string;
  runtime_parity_loop_status: string;
  runtime_parity_loop_stage_refs: string[];
  status_cli_ref: string;
  capabilities_cli_ref: string;
  invocations_cli_ref: string;
  receipts_cli_ref: string;
  signed_evidence_cli_ref: string;
  signed_evidence_verifier_cli_ref: string;
  safe_disable_cli_ref: string;
  status: string;
  runtime_status_ref: string;
  default_profile: string;
  runtime_profile_status: string;
  local_model_readiness: string;
  command_runtime_readiness: string;
  safe_disable_ref: string;
  safe_disable_posture_ref: string;
  safe_disable_active: boolean;
  safe_disable_summary: string;
  item_count: number;
  pending_approval_count: number;
  approved_pending_execution_count: number;
  receipt_recorded_count: number;
  blocked_count: number;
  item_refs: string[];
  approval_envelope_refs: string[];
  pending_runtime_approval_refs: string[];
  execution_result_refs: string[];
  receipt_refs: string[];
  signed_evidence_refs: string[];
  evidence_refs: string[];
  items: FounderLoopRuntimeActionInboxBridgeItem[];
  evidence_timeline: FounderLoopRuntimeEvidenceTimelineItem[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  operator_summary: string;
  action_execution_enabled: boolean;
  arbitrary_command_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  browser_execution_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopRuntimeEvidenceTimelineItem {
  event_ref: string;
  event_kind: string;
  invocation_ref: string;
  receipt_ref?: string | null;
  policy_decision_ref?: string | null;
  action_envelope_ref?: string | null;
  evidence_refs: string[];
  safe_summary: string;
}

export type ActionToolCodeCapabilityKind =
  | "tool_preview"
  | "action_micro_lane"
  | "runtime_micro_lane"
  | "code_workflow";

export type ActionToolCodeLaneStatus =
  | "implemented_preview_only"
  | "implemented_exact_local_mutation_lane"
  | "implemented_exact_approval_required"
  | "proposal_only"
  | "blocked_missing_exact_authority";

export interface ActionToolCodeLaneEntry {
  capability_id: string;
  capability_ref: string;
  lane_ref: string;
  label: string;
  capability_kind: ActionToolCodeCapabilityKind;
  surface: string;
  status: ActionToolCodeLaneStatus;
  side_effect_class: string;
  required_approval_scope: string;
  eligibility_reason: string;
  blocked_reason: string;
  receipt_requirement: string;
  rollback_or_safe_disable_posture: string;
  route_refs: string[];
  cli_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  unblock_prompt_refs: string[];
  operator_visible: boolean;
  inspectable_now: boolean;
  proposal_only: boolean;
  exact_local_mutation_available: boolean;
  exact_runtime_lane_available: boolean;
  generic_tool_execution_enabled: boolean;
  unrestricted_shell_execution_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  plugin_runtime_import_enabled: boolean;
  remote_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ActionToolCodeUnblockPrompt {
  prompt_ref: string;
  title: string;
  target_capability_ref: string;
  blocked_authority_refs: string[];
  copy_ready_prompt: string;
}

export interface ActionToolCodeLaneCatalogReadModel {
  schema_version: "uaa-action-tool-code-lane-catalog.v1";
  contract_ref: string;
  source: "python_core_action_tool_code_lane_catalog_read_model";
  catalog_ref: string;
  route_ref: string;
  cli_ref: string;
  status: string;
  backend_owned: boolean;
  control_center_presentation_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  entry_count: number;
  preview_only_count: number;
  exact_local_mutation_count: number;
  exact_runtime_lane_count: number;
  proposal_only_count: number;
  blocked_count: number;
  entries: ActionToolCodeLaneEntry[];
  unblock_prompts: ActionToolCodeUnblockPrompt[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  operator_summary: string;
  generic_tool_execution_enabled: boolean;
  unrestricted_shell_execution_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  plugin_runtime_import_enabled: boolean;
  remote_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export type FounderLoopActionInboxDecisionLaneId =
  | "needs_approval"
  | "blocked"
  | "draft_only"
  | "cost_blocked"
  | "no_authority"
  | "approved_no_execution"
  | "rejected"
  | "deferred"
  | "receipt_recorded";

export interface FounderLoopActionInboxDecisionLaneItem {
  item_ref: string;
  lane_id: FounderLoopActionInboxDecisionLaneId;
  lane_label: string;
  title: string;
  status: string;
  priority: string;
  action_kind: string;
  side_effect_class: string;
  safe_summary: string;
  why_shown: string;
  next_safe_action: string;
  authority_boundary: string;
  approval_required: boolean;
  approval_envelope_ref?: string | null;
  approval_envelope_status: string;
  approval_scope_ref?: string | null;
  approval_requirement_ref?: string | null;
  expected_receipt_refs: string[];
  expected_receipt_state: string;
  evidence_refs: string[];
  receipt_refs: string[];
  expected_receipt_refs_visible: boolean;
  rollback_ref?: string | null;
  safe_disable_ref?: string | null;
  blocked_authority_refs: string[];
  missing_envelope_field_states: string[];
  cost_state_label: string;
  provider_authority_state_label: string;
  estimated_cost_usd: number;
  max_approved_cost_usd: number;
  provider_ref?: string | null;
  model_profile_ref?: string | null;
  input_metered_units: number;
  output_metered_units: number;
  total_metered_units: number;
  cost_estimate_ref?: string | null;
  captured_usage_ref?: string | null;
  budget_decision_ref?: string | null;
  cost_receipt_refs: string[];
  cost_blocked_state_refs: string[];
  unknown_paid_cost_requires_explicit_approval: boolean;
  frontier_usage_claimed: boolean;
  cost_telemetry_complete: boolean;
  provider_model_refs_present: boolean;
  backend_owned: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  approval_alone_executes: boolean;
  approval_ref_authority: boolean;
  approval_grants_runtime_authority: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopActionInboxDecisionLane {
  lane_id: FounderLoopActionInboxDecisionLaneId;
  label: string;
  status: string;
  safe_summary: string;
  count: number;
  item_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  approval_alone_executes: boolean;
  action_execution_enabled: boolean;
}

export interface FounderLoopActionInboxDecisionLaneReadModel {
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  lane_order: FounderLoopActionInboxDecisionLaneId[];
  lanes: FounderLoopActionInboxDecisionLane[];
  items: FounderLoopActionInboxDecisionLaneItem[];
  blocked_state_refs: string[];
  missing_envelope_fields_fail_safe: boolean;
  cost_posture_visible_before_approval: boolean;
  provider_authority_visible_before_approval: boolean;
  approval_scope_visible_before_approval: boolean;
  expected_receipts_visible_before_approval: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  production_authority_enabled: boolean;
  approval_alone_executes: boolean;
}

export type FounderLoopActionDecisionKind =
  "approve" | "edit" | "reject" | "defer";

export interface FounderLoopActionDecisionRequest {
  decision_reason_ref: string;
  approval_ref?: string | null;
  edited_envelope_ref?: string | null;
  defer_until_ref?: string | null;
  metadata_refs?: string[];
  approval_grants?: unknown[];
}

export interface FounderLoopActionDecisionReceipt {
  contract_ref: string;
  decision_ref: string;
  item_ref: string;
  decision: FounderLoopActionDecisionKind;
  status: string;
  receipt_ref: string;
  audit_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  approval_ref: string;
  approval_status: string;
  approval_reason_refs: string[];
  action_executed: boolean;
  approval_grants_execution: boolean;
  connector_write_performed: boolean;
  memory_write_performed: boolean;
  raw_content_stored: boolean;
  replayed: boolean;
  safe_summary: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  created_at: string;
}

export interface FounderLoopLocalTaskCommitRequest {
  approval_ref: string;
  decision_reason_ref: string;
  metadata_refs?: string[];
}

export interface FounderLoopLocalTaskCommitReceipt {
  contract_ref: string;
  item_ref: string;
  action_kind: "local_task_create";
  local_task_ref: string;
  status: string;
  receipt_ref: string;
  audit_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  evidence_timeline_event_ref: string;
  approval_ref: string;
  approval_status: string;
  approval_reason_refs: string[];
  local_task_created: boolean;
  safe_disable_ref?: string;
  rollback_ref?: string;
  safe_disable_posture_ref?: string;
  safe_disable_enabled?: boolean;
  rollback_execution_enabled?: boolean;
  rollback_blocker_refs?: string[];
  connector_write_performed: boolean;
  shell_subprocess_execution_performed: boolean;
  model_provider_authority_used: boolean;
  memory_write_performed: boolean;
  context_injection_performed: boolean;
  external_side_effect_performed: boolean;
  raw_content_stored: boolean;
  replayed: boolean;
  safe_summary: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  created_at: string;
}

export interface FounderLoopActionEnvelopePromotionRequest {
  today_item_ref: string;
  actor_context: string;
  decision_reason_ref: string;
  risk_class: "low" | "medium" | "high" | "critical";
  priority: "low" | "medium" | "high";
  metadata_refs?: string[];
  estimated_cost_usd?: number;
  max_approved_cost_usd?: number;
  provider_ref?: string;
  model_profile_ref?: string;
  input_metered_units?: number;
  output_metered_units?: number;
  total_metered_units?: number;
  unknown_paid_cost_requires_explicit_approval?: boolean;
  frontier_usage_claimed?: boolean;
}

export interface FounderLoopActionEnvelopePromotionReceipt {
  contract_ref: string;
  today_item_ref: string;
  item_ref: string;
  action_envelope_ref: string;
  status: string;
  receipt_ref: string;
  audit_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  evidence_timeline_event_ref: string;
  action_executed: boolean;
  approval_grants_execution: boolean;
  connector_write_performed: boolean;
  memory_write_performed: boolean;
  raw_content_stored: boolean;
  replayed: boolean;
  safe_summary: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  cost_contract_ref: string;
  estimated_cost_usd: number;
  max_approved_cost_usd: number;
  provider_ref: string;
  model_profile_ref: string;
  input_metered_units: number;
  output_metered_units: number;
  total_metered_units: number;
  cost_estimate_ref: string;
  captured_usage_ref: string;
  budget_decision_ref: string;
  cost_receipt_refs: string[];
  cost_blocked_state_refs: string[];
  cost_state_label: string;
  provider_authority_state_label: string;
  unknown_paid_cost_requires_explicit_approval: boolean;
  frontier_usage_claimed: boolean;
  created_at: string;
}

export type ChatHandoffTarget = "actions" | "plans";

export interface ChatTurnReceiptRequest {
  turn_ref?: string;
  route_ref: string;
  model_ref: string;
  runtime_truth: string;
  auth_truth: string;
  tool_denial_truth: string;
  safe_summary_ref: string;
  turn_harness_binding?: TurnHarnessBindingReadModel;
  evidence_refs?: string[];
  metadata_refs?: string[];
}

export interface ChatTurnReceipt {
  contract_ref: string;
  turn_ref: string;
  route_ref: string;
  model_ref: string;
  runtime_truth: string;
  auth_truth: string;
  tool_denial_truth: string;
  safe_summary_ref: string;
  turn_harness_binding?: TurnHarnessBindingReceiptSummary;
  handoff_refs: string[];
  receipt_ref: string;
  evidence_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  response_visible: boolean;
  prompt_body_visible: boolean;
  completion_body_visible: boolean;
  model_output_authority: boolean;
  tool_execution_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  provider_sdk_call_enabled: boolean;
  web_fetch_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  action_execution_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export interface ChatHandoffRequest {
  handoff_target: ChatHandoffTarget;
  decision_reason_ref: string;
  metadata_refs?: string[];
}

export interface ChatHandoffReceipt {
  contract_ref: string;
  turn_ref: string;
  handoff_target: ChatHandoffTarget;
  handoff_ref: string;
  created_ref: string;
  receipt_ref: string;
  audit_ref: string;
  evidence_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  safe_summary_ref: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  action_executed: boolean;
  plan_executed: boolean;
  connector_write_performed: boolean;
  memory_write_performed: boolean;
  model_output_authority: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export type MemoryReviewDecisionKind =
  | "accept"
  | "correct"
  | "reject"
  | "defer"
  | "merge"
  | "supersede"
  | "forget_request";

export interface MemoryReviewDecisionRequest {
  reviewer_ref: string;
  corrected_summary_ref?: string | null;
  corrected_safe_summary?: string | null;
  source_refs?: string[];
  evidence_refs?: string[];
  metadata_refs?: string[];
  merge_refs?: string[];
  supersedes_refs?: string[];
  forget_request_ref?: string | null;
  blocked_state_refs?: string[];
}

export interface MemoryReviewDecisionReceipt {
  contract_ref: string;
  candidate_ref: string;
  review_ref: string;
  decision: MemoryReviewDecisionKind;
  corrected_summary_ref?: string | null;
  corrected_safe_summary?: string | null;
  source_refs: string[];
  evidence_refs: string[];
  reviewer_ref: string;
  receipt_ref: string;
  decision_ref: string;
  audit_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  evidence_timeline_event_ref: string;
  approval_ref: string;
  approval_status: string;
  approval_reason_refs: string[];
  reviewed_recall_ref?: string | null;
  reviewed_recall_record_ref?: string | null;
  correction_ref?: string | null;
  rejection_ref?: string | null;
  defer_ref?: string | null;
  merge_ref?: string | null;
  supersede_ref?: string | null;
  forget_request_ref?: string | null;
  merge_refs?: string[];
  supersedes_refs?: string[];
  suppressed_recall_record_refs?: string[];
  safe_summary_ref: string;
  blocked_state_refs: string[];
  authority_boundary: string;
  context_injection_authorized: boolean;
  connector_write_authorized: boolean;
  external_crm_sync_authorized: boolean;
  account_sync_authorized: boolean;
  automatic_action_execution_authorized: boolean;
  model_provider_authority_allowed: boolean;
  source_truth_authority: boolean;
  memory_truth_authority: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export interface ManualMemoryCandidateRequest {
  candidate_kind: string;
  title: string;
  safe_summary: string;
  priority?: string;
  reviewer_ref?: string;
  source_refs?: string[];
  provenance_refs?: string[];
  evidence_refs?: string[];
  missing_evidence_refs?: string[];
  related_entity_refs?: string[];
  tag_refs?: string[];
  metadata_refs?: string[];
  blocked_state_refs?: string[];
}

export interface ManualMemoryCandidateReceipt {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  review_ref: string;
  candidate_ref: string;
  candidate_kind: string;
  status: string;
  receipt_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  source_refs: string[];
  provenance_refs: string[];
  evidence_refs: string[];
  missing_evidence_refs: string[];
  related_entity_refs: string[];
  tag_refs: string[];
  metadata_refs: string[];
  safe_summary_ref: string;
  approval_ref?: string | null;
  approval_status?: string;
  approval_reason_refs?: string[];
  blocked_state_refs: string[];
  review_candidate_created: boolean;
  reviewed_recall_record_created: boolean;
  memory_write_performed: boolean;
  memory_delete_performed: boolean;
  memory_export_performed: boolean;
  context_injection_authorized: boolean;
  connector_write_authorized: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export interface FounderLoopMemoryWorkbenchGroup {
  group_id:
    | "needs_review"
    | "conflict"
    | "duplicate"
    | "stale"
    | "missing_evidence"
    | "reviewed"
    | "rejected";
  count: number;
}

export type FounderLoopMemoryLifecycleLaneId =
  | "duplicate_review"
  | "stale_review"
  | "conflict_review"
  | "corrected"
  | "merged"
  | "superseded"
  | "forget_requested";

export interface FounderLoopMemoryLifecycleLane {
  lane_id: FounderLoopMemoryLifecycleLaneId;
  label: string;
  posture_ref: string;
  decision_kind: MemoryReviewDecisionKind;
  count: number;
  item_refs: string[];
  receipt_refs: string[];
  receipt_backed: boolean;
  review_only: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryLifecyclePosture {
  schema_version: string;
  contract_ref: string;
  status: string;
  lanes: FounderLoopMemoryLifecycleLane[];
  decision_receipt_refs_by_kind: Partial<
    Record<MemoryReviewDecisionKind, string[]>
  >;
  receipt_truncation_posture: string;
  receipt_backed_decision_kinds: MemoryReviewDecisionKind[];
  review_only: boolean;
  safe_refs_only: boolean;
  reversible_review_posture: string;
  hard_delete_authorized: boolean;
  memory_export_authorized: boolean;
  automatic_merge_authorized: boolean;
  automatic_supersede_authorized: boolean;
  automatic_forget_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  connector_write_authorized: boolean;
  model_provider_call_authorized: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryLearningPosture {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  control_center_presentation_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  proposal_first_intake: boolean;
  review_required_before_recall: boolean;
  feedback_receipts_supported: boolean;
  correction_receipts_supported: boolean;
  rejection_receipts_supported: boolean;
  forget_request_receipts_supported: boolean;
  forget_execution_authorized: boolean;
  broad_memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  hidden_context_injection_authorized: boolean;
  automatic_context_injection_authorized: boolean;
  memory_truth_authority: boolean;
  policy_override_authorized: boolean;
  action_execution_authorized: boolean;
  connector_write_authorized: boolean;
  model_provider_call_authorized: boolean;
  live_web_fetch_authorized: boolean;
  background_autonomy_authorized: boolean;
  hard_delete_authorized: boolean;
  export_execution_authorized: boolean;
  production_authority_enabled: boolean;
  lifecycle_state_counts: Record<
    | "proposed"
    | "active"
    | "needs_review"
    | "corrected"
    | "rejected"
    | "stale"
    | "forgotten"
    | "blocked",
    number
  >;
  lifecycle_state_refs: string[];
  feedback_flow_refs: string[];
  quality_control_refs: string[];
  context_pack_posture: {
    status: string;
    proposal_count: number;
    proposal_refs: string[];
    context_pack_refs: string[];
    separates_facts_assumptions_memories_unknowns: boolean;
    context_injection_authorized: boolean;
    hidden_prompt_context_authorized: boolean;
    prompt_context_written: boolean;
    provider_model_call_performed: boolean;
    action_execution_authorized: boolean;
  };
  receipt_posture: {
    decision_receipt_count: number;
    accepted_receipt_refs: string[];
    corrected_receipt_refs: string[];
    rejected_receipt_refs: string[];
    forget_request_receipt_refs: string[];
    reviewed_recall_refs: string[];
    receipt_backed_decision_kinds: MemoryReviewDecisionKind[];
  };
  quality_posture: {
    attention_refs: string[];
    quality_issue_refs: string[];
    ranking_contract_ref?: string;
    ranking_strategy_refs: string[];
    search_index_status: FounderLoopMemorySearchIndexStatus;
    semantic_search_enabled: boolean;
    vector_db_enabled: boolean;
    embedding_search_enabled: boolean;
  };
  provenance_posture: {
    provenance_refs: string[];
    provenance_ref_count: number;
    source_refs_required: boolean;
    evidence_refs_required: boolean;
    receipt_refs_required_for_reviewed_recall: boolean;
    safe_summary_only: boolean;
  };
  next_safe_action: string;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryRankingSourceMix {
  source_ref: string;
  count: number;
}

export interface FounderLoopMemoryRankingExcludedRef {
  memory_ref: string;
  reason_refs: string[];
}

export interface FounderLoopMemoryRankingPressureCounts {
  stale: number;
  conflict: number;
  duplicate: number;
  missing_evidence: number;
}

export interface FounderLoopMemorySearchIndexStatus {
  status: string;
  provider_kind?: string;
  fts5_enabled: boolean;
  indexed_record_count: number;
  safe_summary_refs_only: boolean;
  raw_content_indexed: boolean;
  embedding_index_enabled: boolean;
  vector_db_enabled: boolean;
  semantic_search_enabled: boolean;
  hrr_enabled: boolean;
  algebraic_retrieval_enabled: boolean;
}

export interface FounderLoopMemoryBoundedPosture {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  proof_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  control_center_presentation_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  target_posture: {
    supported_target_kinds: string[];
    target_refs: string[];
    target_ref_count: number;
    operator_selected_context_required: boolean;
    automatic_context_injection_authorized: boolean;
    hidden_context_injection_authorized: boolean;
  };
  capacity_posture: {
    visible_item_count: number;
    candidate_count: number;
    context_pack_count: number;
    max_visible_items: number;
    max_provenance_refs: number;
    token_estimate: number;
    token_budget_state: string;
    search_index_status: FounderLoopMemorySearchIndexStatus;
  };
  source_posture: {
    source_refs: string[];
    source_ref_count: number;
    provenance_refs: string[];
    provenance_ref_count: number;
    evidence_refs: string[];
    evidence_ref_count: number;
    receipt_refs: string[];
    receipt_ref_count: number;
    safe_summary_only: boolean;
    source_refs_required: boolean;
  };
  staleness_posture: {
    stale_count: number;
    stale_item_refs: string[];
    stale_state_refs: string[];
    recheck_required_before_recall: boolean;
  };
  why_shown_posture: {
    why_shown_required: boolean;
    why_shown_refs: string[];
    included_reason_refs: string[];
    quality_state_refs: string[];
  };
  quality_review_posture: {
    review_required_before_recall: boolean;
    correction_supported: boolean;
    rejection_supported: boolean;
    correction_receipt_refs: string[];
    rejection_receipt_refs: string[];
    accepted_receipt_refs: string[];
    receipt_backed_decision_kinds: MemoryReviewDecisionKind[];
    reviewed_recall_write_scope_ref: string;
    memory_write_requires_review_receipt: boolean;
    rollback_posture: string;
  };
  context_pack_posture: {
    context_pack_refs: string[];
    proposal_count: number;
    context_pack_preview_only: boolean;
    prompt_context_written: boolean;
    context_injection_authorized: boolean;
    hidden_prompt_context_authorized: boolean;
  };
  automatic_memory_write_authorized: boolean;
  autonomous_memory_write_authorized: boolean;
  hidden_prompt_injection_authorized: boolean;
  external_memory_provider_write_authorized: boolean;
  context_injection_authorized: boolean;
  memory_truth_authority: boolean;
  semantic_provider_enabled: boolean;
  vector_db_enabled: boolean;
  embedding_search_enabled: boolean;
  model_provider_call_authorized: boolean;
  live_web_fetch_authorized: boolean;
  connector_write_authorized: boolean;
  delete_export_execution_authorized: boolean;
  background_autonomy_authorized: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopMemoryHrrReadiness {
  schema_version: string;
  contract_ref: string;
  status: string;
  required_milestone_ref: string;
  hrr_enabled: boolean;
  algebraic_retrieval_enabled: boolean;
  ranking_influence_enabled: boolean;
  shadow_mode_enabled: boolean;
  raw_content_input_enabled: boolean;
  embedding_provider_enabled: boolean;
  vector_db_enabled: boolean;
  context_injection_authorized: boolean;
  action_execution_authorized: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryRankingSummary {
  schema_version: string;
  contract_ref: string;
  status: string;
  query_ref: string;
  safe_query_ref?: string | null;
  query_mode?: string;
  candidate_count: number;
  ranked_candidate_refs: string[];
  included_ranked_refs: string[];
  excluded_refs: FounderLoopMemoryRankingExcludedRef[];
  excluded_ref_count: number;
  score_component_bounds: Record<string, number>;
  source_mix: FounderLoopMemoryRankingSourceMix[];
  pressure_counts: FounderLoopMemoryRankingPressureCounts;
  cache_key: string;
  cache_hit: boolean;
  token_estimate: number;
  rank_signal_refs: string[];
  retrieval_strategy_refs?: string[];
  blocked_authority_refs: string[];
  safe_query_blocked_authority_refs?: string[];
  hrr_readiness?: FounderLoopMemoryHrrReadiness;
  safe_refs_only: boolean;
  lexical_tag_ref_only: boolean;
  embedding_search_enabled: boolean;
  vector_db_enabled: boolean;
  semantic_provider_enabled: boolean;
  context_injection_authorized: boolean;
  memory_write_performed: boolean;
  auto_maintenance_performed: boolean;
  action_execution_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryWorkbenchItem {
  memory_ref: string;
  review_ref: string;
  source: string;
  title: string;
  safe_summary: string;
  candidate_kind: string;
  priority: string;
  status: string;
  review_state: string;
  stale_state: string;
  conflict_state: string;
  side_effect_class: string;
  authority_boundary: string;
  source_refs: string[];
  provenance_refs: string[];
  evidence_refs: string[];
  missing_contract_refs: string[];
  related_entity_refs: string[];
  tag_refs: string[];
  blocked_state_refs: string[];
  receipt_refs: string[];
  quality_state_refs: string[];
  quality_reason_refs: string[];
  why_shown_refs: string[];
  duplicate_key_ref: string;
  conflict_key_ref: string;
  duplicate_of_refs?: string[];
  conflict_with_refs?: string[];
  lifecycle_state_refs?: string[];
  available_lifecycle_decisions?: MemoryReviewDecisionKind[];
  lifecycle_receipt_refs?: string[];
  reversible_review_posture?: string;
  hard_delete_authorized?: boolean;
  automatic_merge_authorized?: boolean;
  automatic_supersede_authorized?: boolean;
  automatic_forget_authorized?: boolean;
  hidden_memory_write_authorized?: boolean;
  group_ids: FounderLoopMemoryWorkbenchGroup["group_id"][];
  rank_score: number;
  rank_components: Record<string, number>;
  score_components?: Record<string, number>;
  retrieval_strategy_refs?: string[];
  included_reason_refs: string[];
  excluded_reason_refs: string[];
  stale_pressure: number;
  conflict_pressure: number;
  duplicate_pressure: number;
  missing_evidence_pressure: number;
  source_mix: FounderLoopMemoryRankingSourceMix[];
  cache_key: string;
  token_estimate: number;
  ranking_blocked_authority_refs: string[];
  why_ranked_refs: string[];
  next_safe_action: string;
  created_at?: string;
}

export interface FounderLoopMemoryWorkbenchHealth {
  schema_version: string;
  pending_review_count: number;
  stale_count: number;
  conflict_count: number;
  duplicate_count: number;
  missing_evidence_count: number;
  reviewed_recall_count: number;
  rejected_count: number;
  needs_attention_refs: string[];
}

export interface FounderLoopMemoryWorkbench {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  groups: FounderLoopMemoryWorkbenchGroup[];
  items: FounderLoopMemoryWorkbenchItem[];
  health: FounderLoopMemoryWorkbenchHealth;
  lifecycle_posture?: FounderLoopMemoryLifecyclePosture;
  learning_posture?: FounderLoopMemoryLearningPosture;
  bounded_memory_posture?: FounderLoopMemoryBoundedPosture;
  decision_receipts: MemoryReviewDecisionReceipt[];
  l1_preview_refs: string[];
  l2_projection_refs: string[];
  l3_projection_refs: string[];
  context_pack_refs: string[];
  ranking: FounderLoopMemoryRankingSummary;
  safe_query_ref?: string | null;
  query_mode?: string;
  retrieval_strategy_refs?: string[];
  search_index_status?: FounderLoopMemorySearchIndexStatus;
  hrr_readiness?: FounderLoopMemoryHrrReadiness;
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  semantic_search_enabled: boolean;
  vector_db_enabled: boolean;
  embedding_search_enabled: boolean;
  context_injection_authorized: boolean;
  memory_truth_authority: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryReview {
  route_ref: string;
  surface_ref: string;
  contract_ref: string;
  legacy_decision_contract_ref: string;
  workbench_route_ref?: string;
  workbench_contract_ref?: string;
  workbench_health?: FounderLoopMemoryWorkbenchHealth;
  workbench_groups?: FounderLoopMemoryWorkbenchGroup[];
  bounded_memory_posture_contract_ref?: string;
  bounded_memory_posture?: FounderLoopMemoryBoundedPosture;
  evidence_memory_loop_binding_contract_ref?: string;
  evidence_memory_loop_binding_read_model?: FounderLoopEvidenceMemoryLoopBindingReadModel;
  decision_route_refs: string[];
  decision_kinds: MemoryReviewDecisionKind[];
  items: FounderLoopMemoryReviewItem[];
  decision_receipts: MemoryReviewDecisionReceipt[];
  decision_receipt_refs: string[];
  decision_count: number;
  idempotency_replay_enabled: boolean;
  idempotency_conflict_rejected: boolean;
  safe_refs_only: boolean;
  raw_content_stored: boolean;
  context_injection_authorized: boolean;
  connector_write_authorized: boolean;
  external_crm_sync_authorized: boolean;
  automatic_action_execution_authorized: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
  authority_boundary: string;
}

export interface FounderLoopPlanSummary {
  plan_ref: string;
  title: string;
  status: string;
  safe_summary: string;
  next_step_summary: string;
  evidence_refs: string[];
  action_envelope_contract_ref?: string;
  action_envelope_ref?: string;
  action_envelope_status?: string;
  action_envelope_safe_summary?: string;
  scope_ref?: string;
  side_effect_class?: string;
  risk_class?: string;
  approval_required?: boolean;
  approval_requirement_ref?: string;
  review_actions?: string[];
  review_posture_refs?: string[];
  expected_receipt_refs?: string[];
  idempotency_key_ref?: string;
  expires_at?: string;
  stale_state?: string;
  rollback_ref?: string;
  safe_disable_ref?: string;
  blocked_state_refs?: string[];
  authority_boundary?: string;
  exact_scope_required?: boolean;
  approval_ref_authority?: boolean;
  approval_grant_capture_enabled?: boolean;
  action_execution_enabled?: boolean;
  tool_execution_enabled?: boolean;
  workflow_execution_enabled?: boolean;
  browser_execution_enabled?: boolean;
  connector_runtime_enabled?: boolean;
  connector_write_enabled?: boolean;
  shell_subprocess_execution_enabled?: boolean;
  model_provider_authority_allowed?: boolean;
  safe_refs_only?: boolean;
  raw_content_included?: boolean;
  action_envelope_cost_contract_ref?: string;
  action_envelope_estimated_cost_usd?: number;
  action_envelope_max_approved_cost_usd?: number;
  action_envelope_provider_ref?: string;
  action_envelope_model_profile_ref?: string;
  action_envelope_input_metered_units?: number;
  action_envelope_output_metered_units?: number;
  action_envelope_total_metered_units?: number;
  action_envelope_cost_estimate_ref?: string;
  action_envelope_captured_usage_ref?: string;
  action_envelope_budget_decision_ref?: string;
  action_envelope_cost_receipt_refs?: string[];
  action_envelope_cost_blocked_state_refs?: string[];
  action_envelope_cost_state_label?: string;
  action_envelope_provider_authority_state_label?: string;
  action_envelope_unknown_paid_cost_requires_explicit_approval?: boolean;
  action_envelope_frontier_usage_claimed?: boolean;
  plan_action_envelope_ref?: string;
  plan_action_scope_ref?: string;
  plan_action_approval_requirement_ref?: string;
  plan_action_review_posture_refs?: string[];
  plan_action_expected_receipt_refs?: string[];
  plan_action_blocked_state_refs?: string[];
  plan_action_authority_boundary?: string;
  task_decomposition_contract_ref?: string;
  task_decomposition_request_ref?: string;
  task_decomposition_original_request_ref?: string;
  task_decomposition_review_envelope_ref?: string;
  task_decomposition_proposal_ref?: string;
  task_decomposition_status?: string;
  task_decomposition_steps?: FounderLoopTaskDecompositionStep[];
  task_decomposition_step_refs?: string[];
  task_decomposition_dependency_refs?: string[];
  task_decomposition_ambiguity_refs?: string[];
  task_decomposition_missing_evidence_refs?: string[];
  task_decomposition_risks?: FounderLoopTaskDecompositionRisk[];
  task_decomposition_risk_class?: string;
  task_decomposition_suggested_action_inbox_proposal_refs?: string[];
  task_decomposition_required_approvals?: string[];
  task_decomposition_blocked_authority_refs?: string[];
  task_decomposition_why_proposed?: string;
  task_decomposition_what_this_affects?: string[];
  task_decomposition_plans_bridge_ref?: string;
  task_decomposition_action_inbox_bridge_ref?: string;
  task_decomposition_review_only?: boolean;
  task_decomposition_proposal_only?: boolean;
  task_decomposition_execution_performed?: boolean;
  task_decomposition_runtime_authority_granted?: boolean;
  task_decomposition_execution_authorized?: boolean;
  task_decomposition_action_execution_enabled?: boolean;
  task_decomposition_tool_execution_enabled?: boolean;
  task_decomposition_workflow_execution_enabled?: boolean;
  task_decomposition_memory_write_authorized?: boolean;
  task_decomposition_context_injection_authorized?: boolean;
  task_decomposition_connector_write_enabled?: boolean;
  task_decomposition_shell_subprocess_execution_enabled?: boolean;
  task_decomposition_browser_network_enabled?: boolean;
  task_decomposition_model_provider_authority_allowed?: boolean;
  task_decomposition_public_beta_claim_enabled?: boolean;
  task_decomposition_production_authority_enabled?: boolean;
  task_decomposition_action_envelope_ref?: string;
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
  source_policy_ref: string;
  source_kind: string;
  source_kind_ref: string;
  source_refs_status: string;
  provenance_refs_status: string;
  source_review_required: boolean;
  source_trust_posture: string;
  safe_summary_only: boolean;
  source_truth_authority: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  account_auth_enabled: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
  source_payload_storage_allowed: boolean;
  prompt_body_storage_allowed: boolean;
  response_body_storage_allowed: boolean;
  provider_body_storage_allowed: boolean;
  path_body_storage_allowed: boolean;
  log_body_storage_allowed: boolean;
  account_ref_storage_allowed: boolean;
  private_content_storage_allowed: boolean;
  connector_runtime_allowed: boolean;
  provider_or_model_authority_allowed: boolean;
  accepted_as_truth: boolean;
  decision_contract_ref: string;
  available_decision_states: string[];
  decision_capture_status: string;
  decision_required_ref_fields: string[];
  decision_actor_ref: string;
  decision_source_provenance_contract_ref: string;
  decision_source_kind: string;
  decision_source_trust_posture: string;
  decision_redaction_status: string;
  decision_audit_refs: string[];
  decision_receipt_refs: string[];
  decision_blocked_state_refs: string[];
  decision_stale_state: string;
  decision_retention_posture: string;
  decision_correction_posture: string;
  decision_authority_boundary: string;
  decision_review_only: boolean;
  memory_delete_authorized: boolean;
  memory_export_authorized: boolean;
  retention_execution_authorized: boolean;
  business_memory_quality_contract_ref: string;
  business_memory_candidate_ref: string;
  business_memory_candidate_kind: string;
  business_memory_candidate_kind_ref: string;
  business_memory_source_provenance_contract_ref: string;
  business_memory_source_kind: string;
  business_memory_source_trust_posture: string;
  business_memory_redaction_status: string;
  business_memory_quality_state_refs: string[];
  business_memory_quality_posture: string;
  business_memory_review_state: string;
  business_memory_correction_path: string;
  business_memory_stale_state: string;
  business_memory_retention_posture: string;
  business_memory_delete_posture: string;
  business_memory_export_posture: string;
  business_memory_related_entity_refs: string[];
  business_memory_duplicate_of_refs: string[];
  business_memory_conflict_with_refs: string[];
  business_memory_blocker_refs: string[];
  business_memory_surface_refs: string[];
  business_memory_next_safe_action: string;
  business_memory_safe_refs_only: boolean;
  business_memory_review_required_before_recall: boolean;
  business_memory_accepted_as_recall: boolean;
  business_memory_write_authorized: boolean;
  business_memory_delete_authorized: boolean;
  business_memory_export_authorized: boolean;
  business_memory_crm_write_authorized: boolean;
  business_memory_account_sync_authorized: boolean;
  business_memory_context_injection_authorized: boolean;
  business_memory_authority_boundary: string;
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

export interface FounderLoopEvidenceTimelineItem {
  timeline_item_ref: string;
  item_kind: string;
  title: string;
  safe_summary: string;
  history_contract_ref: string;
  history_answers: FounderLoopEvidenceHistoryAnswers;
  source_refs: string[];
  status_refs: string[];
  related_route_refs: string[];
  side_effect_class: string;
  authority_posture: string;
  approval_posture: string;
  approval_ref_authority: boolean;
  rollback_execution_enabled: boolean;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  raw_evidence_included: boolean;
  receipt_refs: string[];
  audit_refs: string[];
  idempotency_refs?: string[];
  replay_refs: string[];
  rollback_refs: string[];
  rollback_blockers: string[];
  latency_refs: string[];
  foundation_gate_refs: string[];
  redaction_status: string;
  stale_state: string;
  missing_evidence_posture: string;
  blocked_states: string[];
  next_safe_action: string;
  created_at?: string;
}

export type FounderLoopEvidenceEventType =
  | "action_envelope_created"
  | "action_decision_recorded"
  | "local_task_created"
  | "chat_turn_receipt_recorded"
  | "chat_handoff_created"
  | "memory_review_decision_recorded";

export type FounderLoopEvidenceGroupKind =
  "today_item" | "action" | "chat_turn" | "memory_candidate";

export interface FounderLoopEvidenceTimelineEvent {
  event_ref: string;
  event_type: FounderLoopEvidenceEventType;
  event_type_ref: string;
  group_kind: FounderLoopEvidenceGroupKind;
  group_ref: string;
  group_label: string;
  timeline_item_ref: string;
  item_kind: string;
  title: string;
  safe_summary: string;
  history_answers: FounderLoopEvidenceHistoryAnswers;
  source_refs: string[];
  status_refs: string[];
  related_route_refs: string[];
  receipt_refs: string[];
  approval_refs: string[];
  idempotency_refs: string[];
  audit_refs: string[];
  rollback_refs: string[];
  rollback_blockers: string[];
  blocked_states: string[];
  rollback_posture: string;
  authority_posture: string;
  redaction_status: string;
  raw_evidence_included: boolean;
  approval_ref_authority: boolean;
  rollback_execution_enabled: boolean;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  created_at?: string;
}

export interface FounderLoopEvidenceTimelineGroup {
  group_ref: string;
  group_kind: FounderLoopEvidenceGroupKind;
  group_label: string;
  event_count: number;
  event_refs: string[];
  event_types: FounderLoopEvidenceEventType[];
  receipt_refs: string[];
  approval_refs: string[];
  idempotency_refs: string[];
  blocked_states: string[];
  rollback_posture: string;
}

export interface FounderLoopOperatorRunBorrowedPattern {
  pattern_id: string;
  label: string;
  safe_summary: string;
  implemented: boolean;
  source_ref: string;
}

export interface FounderLoopOperatorRunCostUsage {
  schema_version: string;
  contract_ref: string;
  cost_event_ref: string;
  cost_estimate_ref: string;
  captured_usage_ref: string;
  budget_decision_ref: string;
  source_event_ref: string;
  provider_ref: string;
  model_profile_ref: string;
  provider_model_ref_status: string;
  usage_capture_status: string;
  cost_capture_status: string;
  cost_state_label: string;
  provider_authority_state_label: string;
  frontier_usage_claimed: boolean;
  frontier_ai_routing_allowed: boolean;
  input_metered_units: number;
  output_metered_units: number;
  total_metered_units: number;
  estimated_cost_usd: number;
  captured_cost_usd: number;
  max_approved_cost_usd: number;
  unknown_cost: boolean;
  approval_required_for_unknown_paid_cost: boolean;
  cost_governor_ref: string;
  cost_governor_allowed: boolean;
  cost_governor_decision_status: string;
  cost_governor_reason_refs: string[];
  budget_status_ref: string;
  cost_receipt_refs: string[];
  cost_blocked_state_refs: string[];
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
}

export interface FounderLoopOperatorRunEvent {
  run_event_ref: string;
  event_ref: string;
  event_kind: string;
  event_source: string;
  llm_role_projection: string;
  operator_state: string;
  approval_state: string;
  completion_state: string;
  completion_claim_allowed: boolean;
  safe_summary: string;
  condensed_summary_ref: string;
  source_refs: string[];
  status_refs: string[];
  receipt_refs: string[];
  approval_refs: string[];
  audit_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  blocked_state_refs: string[];
  evidence_refs: string[];
  related_route_refs: string[];
  authority_boundary: string;
  cost_usage: FounderLoopOperatorRunCostUsage;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
  provider_model_authority_allowed: boolean;
}

export interface FounderLoopOperatorRunControlSummary {
  states: string[];
  state_refs: string[];
  waiting_for_approval_count: number;
  receipt_recorded_count: number;
  blocked_count: number;
  needs_evidence_count: number;
  stuck_detection_status: string;
  pause_resume_status: string;
  goal_completion_status: string;
}

export interface FounderLoopFrontierAiUsageSummary {
  schema_version: string;
  contract_ref: string;
  status: string;
  provider_model_authority_allowed: boolean;
  provider_sdk_call_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
  estimated_total_cost_usd: number;
  captured_total_cost_usd: number;
  input_metered_units: number;
  output_metered_units: number;
  total_metered_units: number;
  unknown_paid_cost_requires_approval_before_routing: boolean;
  cost_governor_ref: string;
  budget_status_ref: string;
  cost_event_refs: string[];
  cost_receipt_refs: string[];
  cost_blocked_state_refs: string[];
}

export interface FounderLoopOperatorRunTimeline {
  schema_version: string;
  contract_ref: string;
  status: string;
  source: string;
  route_ref: string;
  frontend_route_refs: string[];
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  provider_model_authority_allowed: boolean;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
  borrowed_patterns: FounderLoopOperatorRunBorrowedPattern[];
  event_count: number;
  group_count: number;
  narrative_item_count: number;
  run_events: FounderLoopOperatorRunEvent[];
  run_control_summary: FounderLoopOperatorRunControlSummary;
  frontier_ai_usage_summary: FounderLoopFrontierAiUsageSummary;
  blocked_state_refs: string[];
  authority_boundary: string;
}

export interface FounderLoopEvidenceNarrativeEntry {
  narrative_ref: string;
  event_ref: string;
  timeline_item_ref: string;
  group_ref: string;
  group_kind: string;
  event_type: string;
  title: string;
  what_happened: string;
  why_recorded: string;
  approval_posture: string;
  change_summary: string;
  remaining_blocked: string;
  inspection_summary: string;
  source_refs: string[];
  status_refs: string[];
  receipt_refs: string[];
  approval_refs: string[];
  audit_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  evidence_refs: string[];
  blocked_state_refs: string[];
  raw_content_included: boolean;
  approval_ref_authority: boolean;
  rollback_execution_enabled: boolean;
  action_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  connector_write_enabled: boolean;
  connector_runtime_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  public_beta_enabled: boolean;
  distribution_enabled: boolean;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopEvidenceTimelineNarrativeReadModel {
  schema_version: string;
  contract_ref: string;
  source: string;
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  narrative_from_existing_refs_only: boolean;
  raw_content_included: boolean;
  entry_count: number;
  event_count: number;
  group_count: number;
  narrative_item_count: number;
  entries: FounderLoopEvidenceNarrativeEntry[];
  narrative_refs: string[];
  event_refs: string[];
  timeline_item_refs: string[];
  group_refs: string[];
  receipt_refs: string[];
  approval_refs: string[];
  audit_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  evidence_refs: string[];
  blocked_state_refs: string[];
  authority_boundary: string;
  next_safe_action: string;
  approval_ref_authority: boolean;
  rollback_execution_enabled: boolean;
  action_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  connector_write_enabled: boolean;
  connector_runtime_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  public_beta_enabled: boolean;
  distribution_enabled: boolean;
  prompt_content_stored: boolean;
  response_content_stored: boolean;
  provider_exchange_content_stored: boolean;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
}

export type FounderLoopEvidenceAuditGroupKind =
  | "plan_changes"
  | "approval_waits"
  | "action_proposals"
  | "execution_receipts"
  | "memory_proposals_review_decisions"
  | "blocked_no_go_events"
  | "recovery_events";

export interface FounderLoopEvidenceAuditReceiptEnvelope {
  envelope_ref: string;
  receipt_ref: string;
  receipt_recorded: boolean;
  run_ref: string;
  action_ref: string;
  approval_ref: string;
  event_ref: string;
  timeline_item_ref: string;
  group_ref: string;
  side_effect_class: string;
  authority_decision_ref: string;
  input_ref: string;
  output_ref: string;
  artifact_hash_ref: string;
  timestamp_ref: string;
  verifier_version_ref: string;
  redaction_status: string;
  safe_summary: string;
  route_refs: string[];
  evidence_refs: string[];
  audit_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  blocked_state_refs: string[];
  missing_receipt_refs: string[];
  raw_content_included: boolean;
  approval_ref_authority: boolean;
  action_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_write_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopEvidenceAuditGroup {
  group_ref: string;
  group_kind: FounderLoopEvidenceAuditGroupKind;
  label: string;
  status: string;
  safe_summary: string;
  event_refs: string[];
  timeline_item_refs: string[];
  receipt_refs: string[];
  approval_refs: string[];
  audit_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  evidence_refs: string[];
  missing_receipt_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopEvidenceAuditReceiptSpine {
  schema_version: string;
  contract_ref: string;
  source: string;
  status: string;
  backend_owned: boolean;
  control_center_presentation_only: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  raw_content_included: boolean;
  route_refs: string[];
  cli_ref: string;
  receipt_envelope_field_refs: string[];
  timeline_group_kinds: FounderLoopEvidenceAuditGroupKind[];
  group_count: number;
  envelope_count: number;
  missing_receipt_count: number;
  groups: FounderLoopEvidenceAuditGroup[];
  receipt_envelopes: FounderLoopEvidenceAuditReceiptEnvelope[];
  receipt_refs: string[];
  missing_receipt_refs: string[];
  evidence_refs: string[];
  audit_refs: string[];
  approval_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  blocked_state_refs: string[];
  portable_evidence_posture: string;
  redaction_posture: string;
  authority_boundary: string;
  next_safe_action: string;
  approval_ref_authority: boolean;
  action_execution_enabled: boolean;
  tool_execution_enabled: boolean;
  connector_write_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  external_export_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopEvidenceMemoryEvidenceBinding {
  binding_ref: string;
  timeline_item_ref: string;
  event_ref: string;
  event_type: string;
  group_ref: string;
  title: string;
  why_recorded: string;
  source_refs: string[];
  action_refs: string[];
  run_refs: string[];
  proof_refs: string[];
  shared_loop_refs: string[];
  shared_run_refs: string[];
  shared_action_refs: string[];
  shared_proof_refs: string[];
  approval_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  memory_candidate_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopEvidenceMemoryMemoryBinding {
  binding_ref: string;
  memory_candidate_ref: string;
  review_ref: string;
  title: string;
  why_shown: string;
  source_refs: string[];
  why_shown_refs: string[];
  related_action_refs: string[];
  related_run_refs: string[];
  related_proof_refs: string[];
  shared_loop_refs: string[];
  shared_run_refs: string[];
  shared_action_refs: string[];
  shared_proof_refs: string[];
  related_evidence_refs: string[];
  decision_receipt_refs: string[];
  blocked_authority_refs: string[];
  reviewed_recall_only: boolean;
  write_posture: string;
  reviewed_memory_write_scope_ref: string;
  reviewed_memory_write_authorized: boolean;
  broad_memory_write_blocked: boolean;
  memory_write_safe_disable_ref: string;
  memory_write_rollback_ref: string;
  context_posture: string;
  next_safe_action: string;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  automatic_memory_write_authorized: boolean;
}

export interface FounderLoopEvidenceMemoryLoopBindingReadModel {
  schema_version: "evidence-memory-loop-binding.v1";
  contract_ref: string;
  source: string;
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  route_refs: string[];
  cli_ref: string;
  evidence_binding_count: number;
  memory_binding_count: number;
  evidence_bindings: FounderLoopEvidenceMemoryEvidenceBinding[];
  memory_bindings: FounderLoopEvidenceMemoryMemoryBinding[];
  evidence_refs: string[];
  memory_candidate_refs: string[];
  action_refs: string[];
  run_refs: string[];
  proof_refs: string[];
  receipt_refs: string[];
  shared_loop_ref: string;
  shared_run_refs: string[];
  shared_action_refs: string[];
  shared_proof_refs: string[];
  reviewed_memory_write_scope_ref: string;
  reviewed_memory_write_authorized_decisions: string[];
  reviewed_memory_write_authorized: boolean;
  broad_memory_write_blocked: boolean;
  memory_write_safe_disable_ref: string;
  memory_write_rollback_ref: string;
  promotion_path_refs: string[];
  blocked_authority_refs: string[];
  operator_summary: string;
  next_safe_action: string;
  authority_boundary: string;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  memory_delete_enabled: boolean;
  memory_export_enabled: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopEvidenceTimelineIndex {
  schema_version: string;
  contract_ref: string;
  status: string;
  surface: string;
  route_ref: string;
  frontend_route_ref: string;
  source_today_route_ref: string;
  storage_ref: string;
  side_effect_class: string;
  read_only: boolean;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  raw_content_stored: boolean;
  approval_ref_authority: boolean;
  rollback_execution_enabled: boolean;
  memory_truth_authority: boolean;
  context_injection_authorized: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  production_authority_enabled: boolean;
  event_type_refs: string[];
  event_types: FounderLoopEvidenceEventType[];
  group_kinds: FounderLoopEvidenceGroupKind[];
  event_type_counts: Record<FounderLoopEvidenceEventType, number>;
  event_count: number;
  group_count: number;
  groups: FounderLoopEvidenceTimelineGroup[];
  events: FounderLoopEvidenceTimelineEvent[];
  evidence_audit_receipt_spine_contract_ref?: string;
  evidence_audit_receipt_spine?: FounderLoopEvidenceAuditReceiptSpine;
  operator_run_timeline?: FounderLoopOperatorRunTimeline;
  founder_loop_runs_integration_contract_ref?: string;
  founder_loop_runs_integration_read_model?: FounderLoopRunsIntegrationReadModel;
  loop_trace_refs?: FounderLoopTraceRefs;
  evidence_memory_loop_binding_contract_ref?: string;
  evidence_memory_loop_binding_read_model?: FounderLoopEvidenceMemoryLoopBindingReadModel;
  narrative_contract_ref?: string;
  narrative_read_model?: FounderLoopEvidenceTimelineNarrativeReadModel;
  narrative_items?: FounderLoopEvidenceTimelineItem[];
  review_answer_refs?: Record<
    | "proposed"
    | "decided"
    | "changed"
    | "denied"
    | "skipped"
    | "corrected"
    | "blocked"
    | "reversible_safe_disabled",
    string[]
  >;
  receipt_refs: string[];
  approval_refs: string[];
  idempotency_refs: string[];
  rollback_refs: string[];
  blocked_states: string[];
  authority_boundary: string;
}

export interface FounderLoopEvidenceHistoryQuestion {
  key:
    | "proposed"
    | "approved"
    | "happened"
    | "changed"
    | "undoable"
    | "stale"
    | "blocked";
  question: string;
  required: boolean;
}

export interface FounderLoopEvidenceHistoryAnswer {
  question: string;
  answer: string;
  refs: string[];
  status: string;
}

export interface FounderLoopEvidenceHistoryAnswers {
  proposed: FounderLoopEvidenceHistoryAnswer;
  approved: FounderLoopEvidenceHistoryAnswer;
  happened: FounderLoopEvidenceHistoryAnswer;
  changed: FounderLoopEvidenceHistoryAnswer;
  undoable: FounderLoopEvidenceHistoryAnswer;
  stale: FounderLoopEvidenceHistoryAnswer;
  blocked: FounderLoopEvidenceHistoryAnswer;
}

export interface FounderLoopEvidenceHistorySurfaceBinding {
  surface: string;
  current_status: string;
  required_history_keys: string[];
  authority_boundary: string;
}

export interface FounderLoopMemorySourcePolicy {
  source_kind: string;
  source_kind_ref: string;
  safe_ref_prefix: string;
  safe_summary_required: boolean;
  review_required: boolean;
  trusted_without_review: boolean;
  source_payload_storage_allowed: boolean;
  automatic_memory_write_allowed: boolean;
  context_injection_allowed: boolean;
  connector_runtime_allowed: boolean;
  provider_or_model_authority_allowed: boolean;
  account_auth_allowed: boolean;
}

export interface FounderLoopMemorySourceReviewPosture {
  review_required_before_recall: boolean;
  source_summary_trusted_without_review: boolean;
  external_assistant_summary_trusted_without_review: boolean;
  local_model_summary_trusted_without_review: boolean;
  automatic_memory_write_enabled: boolean;
  hidden_context_injection_enabled: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  provider_or_model_authority_allowed: boolean;
  source_payload_storage_allowed: boolean;
  private_content_storage_allowed: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryReviewDecisionState {
  decision_state: string;
  decision_state_ref: string;
  review_required: boolean;
  actor_ref_required: boolean;
  source_refs_required: boolean;
  provenance_refs_required: boolean;
  evidence_refs_required: boolean;
  audit_refs_required: boolean;
  receipt_refs_required: boolean;
  blocked_state_refs_required: boolean;
  writes_authorized: boolean;
  deletes_authorized: boolean;
  exports_authorized: boolean;
  context_injection_authorized: boolean;
  accepted_as_recall: boolean;
}

export interface FounderLoopMemoryReviewDecisionAuthorityPosture {
  review_only: boolean;
  memory_write_authorized: boolean;
  memory_delete_authorized: boolean;
  memory_export_authorized: boolean;
  context_injection_authorized: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  provider_or_model_authority_allowed: boolean;
  source_truth_authority: boolean;
  accepted_as_recall: boolean;
  retention_execution_authorized: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopBusinessMemoryCandidateKind {
  candidate_kind: string;
  candidate_kind_ref: string;
  review_required: boolean;
  safe_summary_only: boolean;
  source_refs_required: boolean;
  provenance_refs_required: boolean;
  evidence_refs_required: boolean;
  quality_posture_required: boolean;
  correction_path_required: boolean;
  retention_delete_export_posture_required: boolean;
  crm_write_authorized: boolean;
  account_sync_authorized: boolean;
  context_injection_authorized: boolean;
  accepted_as_recall: boolean;
}

export interface FounderLoopBusinessMemoryQualityState {
  quality_state: string;
  quality_state_ref: string;
  blocks_unreviewed_recall: boolean;
  requires_operator_review: boolean;
  requires_safe_refs: boolean;
  requires_correction_path: boolean;
  is_blocking_posture: boolean;
  authorizes_memory_write: boolean;
  authorizes_crm_write: boolean;
  authorizes_context_injection: boolean;
}

export interface FounderLoopBusinessMemorySurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopBusinessMemoryAuthorityPosture {
  safe_refs_only: boolean;
  review_required_before_recall: boolean;
  memory_write_authorized: boolean;
  memory_delete_authorized: boolean;
  memory_export_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  external_crm_write_authorized: boolean;
  account_sync_authorized: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  provider_or_model_authority_allowed: boolean;
  source_truth_authority: boolean;
  accepted_as_recall: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopActionEnvelopeReviewPosture {
  review_action: string;
  review_posture_ref: string;
  exact_scope_required: boolean;
  safe_refs_required: boolean;
  receipt_refs_required: boolean;
  grants_execution_authority: boolean;
  captures_approval_grant: boolean;
}

export interface FounderLoopActionEnvelopeSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopActionEnvelopeAuthorityPosture {
  safe_refs_only: boolean;
  exact_scope_required: boolean;
  approval_required_before_mutation: boolean;
  approval_ref_authority: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  state_change_enabled: boolean;
  tool_execution_enabled: boolean;
  workflow_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  model_provider_authority_allowed: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopPlansToActionsBridgeItem {
  item_ref: string;
  source_plan_ref: string;
  linked_action_item_ref?: string | null;
  plan_title: string;
  plan_status: string;
  safe_summary: string;
  why_proposed: string;
  risk_class: string;
  action_envelope_ref: string;
  action_scope_ref: string;
  approval_requirement_ref: string;
  task_decomposition_proposal_ref?: string | null;
  task_decomposition_review_envelope_ref?: string | null;
  task_decomposition_action_inbox_bridge_ref?: string | null;
  review_receipt_labels: string[];
  expected_receipt_refs: string[];
  receipt_refs: string[];
  rollback_ref: string;
  safe_disable_ref: string;
  evidence_refs: string[];
  step_refs: string[];
  risk_refs: string[];
  ambiguity_refs: string[];
  missing_evidence_refs: string[];
  blocked_authority_refs: string[];
  work_classification?: FounderLoopWorkClassification;
  delegation_proposal?: FounderLoopDelegationProposal;
  cache_context_economics?: FounderLoopCacheContextEconomics;
  next_safe_action: string;
  backend_owned: boolean;
  review_only: boolean;
  proposal_only: boolean;
  exact_scope_required: boolean;
  expected_receipts_required: boolean;
  rollback_required: boolean;
  safe_disable_required: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  approval_ref_authority: boolean;
  approval_grant_capture_enabled: boolean;
  approval_alone_executes: boolean;
  execution_authorized: boolean;
  execution_performed: boolean;
  action_execution_enabled: boolean;
  action_execution_performed: boolean;
  tool_execution_enabled: boolean;
  tool_execution_performed: boolean;
  workflow_execution_enabled: boolean;
  workflow_execution_performed: boolean;
  model_provider_call_enabled: boolean;
  model_provider_authority_allowed: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  shell_subprocess_execution_performed: boolean;
  browser_execution_enabled: boolean;
  browser_execution_performed: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  connector_write_performed: boolean;
  memory_write_authorized: boolean;
  memory_write_performed: boolean;
  context_injection_authorized: boolean;
  context_injection_performed: boolean;
  automatic_planning_authority_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopPlansToActionsBridgeReadModel {
  schema_version: "product-loop-006-plans-to-actions.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  item_count: number;
  items: FounderLoopPlansToActionsBridgeItem[];
  plan_refs: string[];
  action_inbox_item_refs: string[];
  task_decomposition_proposal_refs: string[];
  expected_receipt_refs: string[];
  rollback_refs: string[];
  safe_disable_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  approval_ref_authority: boolean;
  approval_grant_capture_enabled: boolean;
  approval_alone_executes: boolean;
  execution_authorized: boolean;
  execution_performed: boolean;
  action_execution_enabled: boolean;
  action_execution_performed: boolean;
  tool_execution_enabled: boolean;
  tool_execution_performed: boolean;
  workflow_execution_enabled: boolean;
  workflow_execution_performed: boolean;
  model_provider_call_enabled: boolean;
  model_provider_authority_allowed: boolean;
  provider_model_call_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  shell_subprocess_execution_performed: boolean;
  browser_execution_enabled: boolean;
  browser_execution_performed: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  connector_write_performed: boolean;
  memory_write_authorized: boolean;
  memory_write_performed: boolean;
  context_injection_authorized: boolean;
  context_injection_performed: boolean;
  automatic_planning_authority_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopChatOperatorSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopChatOperatorAuthorityPosture {
  safe_refs_only: boolean;
  response_visible: boolean;
  prompt_body_visible: boolean;
  completion_body_visible: boolean;
  model_output_authority: boolean;
  tool_execution_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  provider_sdk_call_enabled: boolean;
  web_fetch_enabled: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  action_execution_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopGovernedCodeWorkbenchSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopGovernedCodeWorkbenchAuthorityPosture {
  safe_refs_only: boolean;
  repo_local_scope_required: boolean;
  safe_diff_summary_only: boolean;
  validation_required_before_apply: boolean;
  approval_required_before_apply: boolean;
  atomic_apply_required: boolean;
  rollback_receipt_required: boolean;
  audit_required: boolean;
  redaction_required: boolean;
  apply_execution_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  direct_file_write_enabled: boolean;
  unrestricted_shell_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  remote_execution_enabled: boolean;
  broad_coding_agent_autonomy_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  web_fetch_enabled: boolean;
  connector_write_enabled: boolean;
  diff_body_storage_enabled: boolean;
  production_authority_enabled: boolean;
}

export type OperatorWorkspaceSpineLaneKind =
  | "workspace_status"
  | "git_posture"
  | "preview_status"
  | "run_logs"
  | "coworker_handoff";

export interface OperatorWorkspaceSpineLane {
  lane_ref: string;
  lane_kind: OperatorWorkspaceSpineLaneKind;
  label: string;
  status: string;
  safe_summary: string;
  current_posture_ref: string;
  source_refs: string[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  read_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  runtime_execution_enabled: boolean;
  mutation_enabled: boolean;
}

export interface OperatorWorkspaceSpineReadModel {
  schema_version: "operator_workspace_spine_read_model.v1";
  contract_ref: string;
  source:
    | "python_core_operator_workspace_spine_read_model"
    | "mock_operator_workspace_spine_non_authoritative";
  backend_owned: boolean;
  status: string;
  route_ref: string;
  cli_ref: string;
  workspace_ref: string;
  workspace_status_ref: string;
  repo_scope_ref: string;
  git_posture_ref: string;
  preview_status_ref: string;
  run_log_posture_ref: string;
  coworker_handoff_ref: string;
  lane_order: OperatorWorkspaceSpineLaneKind[];
  lanes: OperatorWorkspaceSpineLane[];
  proof_refs: string[];
  evidence_refs: string[];
  safe_disable_refs: string[];
  rollback_refs: string[];
  blocked_authority_refs: string[];
  promotion_path_refs: string[];
  route_refs: string[];
  docs_refs: string[];
  verifier_refs: string[];
  full_strength_goal: string;
  repo_safe_scope: string;
  blocked_authority_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  read_only: boolean;
  control_center_presentation_only: boolean;
  raw_path_persistence_enabled: boolean;
  raw_log_persistence_enabled: boolean;
  file_write_enabled: boolean;
  git_mutation_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_automation_enabled: boolean;
  dev_server_start_enabled: boolean;
  provider_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopCrossSurfaceMemoryIntakeProposal {
  contract_ref: string;
  proposal_ref: string;
  surface: string;
  source_kind: string;
  candidate_kind: string;
  candidate_ref: string;
  safe_summary: string;
  source_refs: string[];
  source_provenance_contract_ref: string;
  memory_review_decision_contract_ref: string;
  business_memory_quality_contract_ref: string;
  source_trust_posture: string;
  provenance_refs: string[];
  evidence_refs: string[];
  quality_state_refs: string[];
  missing_evidence_refs: string[];
  missing_evidence_posture: string;
  confidence_posture: string;
  stale_state: string;
  next_safe_action: string;
  review_queue_ref: string;
  review_required: boolean;
  safe_summary_only: boolean;
  source_payload_storage_allowed: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  provider_call_enabled: boolean;
  account_fetch_enabled: boolean;
  browser_import_enabled: boolean;
  shell_history_import_enabled: boolean;
  raw_file_import_enabled: boolean;
  connector_runtime_enabled: boolean;
  source_truth_authority: boolean;
  accepted_as_recall: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopCrossSurfaceMemoryIntakeSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopCrossSurfaceMemoryIntakeAuthorityPosture {
  safe_refs_only: boolean;
  review_required: boolean;
  safe_summary_only: boolean;
  source_payload_storage_allowed: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  provider_call_enabled: boolean;
  account_fetch_enabled: boolean;
  browser_import_enabled: boolean;
  shell_history_import_enabled: boolean;
  raw_file_import_enabled: boolean;
  connector_runtime_enabled: boolean;
  source_truth_authority: boolean;
  accepted_as_recall: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryToLoopItem {
  contract_ref: string;
  loop_item_ref: string;
  surface: string;
  loop_binding_state: string;
  memory_candidate_ref: string;
  review_ref: string;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  accepted_recall_refs: string[];
  correction_refs: string[];
  rejected_item_refs: string[];
  follow_up_commitment_refs: string[];
  stale_state: string;
  missing_evidence_refs: string[];
  missing_evidence_posture: string;
  side_effect_class: string;
  approval_posture: string;
  next_safe_action: string;
  review_required: boolean;
  safe_refs_only: boolean;
  memory_write_authorized: boolean;
  automatic_recall_enabled: boolean;
  context_injection_authorized: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  source_truth_authority: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryDerivedActionProposal {
  contract_ref: string;
  proposal_ref: string;
  source_memory_ref: string;
  source_loop_item_ref: string;
  source_review_ref: string;
  source_intake_proposal_ref?: string | null;
  safe_summary: string;
  source_refs: string[];
  provenance_refs: string[];
  evidence_refs: string[];
  side_effect_class: string;
  risk_class: string;
  approval_required: boolean;
  approval_posture: string;
  approval_requirement_ref: string;
  action_envelope_ref: string;
  scope_ref: string;
  review_posture_refs: string[];
  expected_receipt_refs: string[];
  idempotency_key_ref: string;
  expires_at: string;
  rollback_ref: string;
  safe_disable_ref: string;
  next_safe_action: string;
  stale_state: string;
  missing_evidence_refs: string[];
  blocked_state_refs: string[];
  memory_write_authorized: boolean;
  automatic_recall_enabled: boolean;
  context_injection_authorized: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  source_truth_authority: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryToLoopSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopMemoryToLoopAuthorityPosture {
  safe_refs_only: boolean;
  review_required: boolean;
  memory_write_authorized: boolean;
  automatic_recall_enabled: boolean;
  context_injection_authorized: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  connector_write_enabled: boolean;
  account_sync_enabled: boolean;
  source_truth_authority: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryContextPackProposal {
  context_pack_ref: string;
  proposal_ref: string;
  safe_summary: string;
  query_ref?: string | null;
  safe_query_ref?: string | null;
  query_mode?: string;
  status?: string;
  side_effect_class?: string;
  risk_class?: string;
  approval_posture?: string;
  next_safe_action?: string;
  source_memory_record_refs?: string[];
  l1_preview_refs?: string[];
  l2_projection_refs?: string[];
  l3_representation_refs?: string[];
  source_refs?: string[];
  evidence_refs?: string[];
  receipt_refs?: string[];
  observed_ref?: string | null;
  observer_ref?: string | null;
  representation_scope_ref?: string | null;
  score_components?: Record<string, number>;
  retrieval_strategy_refs?: string[];
  missing_evidence_refs?: string[];
  blocked_state_refs?: string[];
  internal_action_proposal_refs?: string[];
  internal_action_receipt_refs?: string[];
  phase6_1_internal_action_proposal_status?: string;
}

export type FounderLoopMemoryFeedbackKind =
  "helpful" | "unhelpful" | "stale" | "conflict" | "not_relevant";

export interface FounderLoopMemoryFeedbackRequest {
  memory_record_ref: string;
  feedback_kind: FounderLoopMemoryFeedbackKind;
  reviewer_ref?: string;
  source_refs: string[];
  evidence_refs: string[];
  note_ref?: string | null;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryFeedbackReceipt {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  receipt_ref: string;
  memory_record_ref: string;
  feedback_kind: FounderLoopMemoryFeedbackKind;
  reviewer_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  approval_ref: string;
  approval_status: string;
  approval_reason_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  note_ref?: string | null;
  trust_delta: number;
  trust_score_after: number;
  stale_state_after: string;
  conflict_state_after: string;
  blocked_state_refs: string[];
  receipt_recorded: boolean;
  reviewed_recall_record_created: boolean;
  memory_delete_performed: boolean;
  memory_export_performed: boolean;
  context_injection_authorized: boolean;
  connector_write_authorized: boolean;
  automatic_action_execution_authorized: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export interface FounderLoopMemoryRetrievalRankSignal {
  rank_signal_ref: string;
  memory_ref: string;
  rank_score: number;
  included: boolean;
  source_ref: string;
  quality_state_refs: string[];
  why_shown_refs: string[];
  pressure_score: number;
}

export interface FounderLoopMemoryRetrievalDiagnostics {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  generated_at: string;
  candidate_count: number;
  included_count: number;
  excluded_count: number;
  included_refs: string[];
  excluded_refs: string[];
  excluded_reason_refs: string[];
  rank_signals: FounderLoopMemoryRetrievalRankSignal[];
  source_mix: Array<{ source_ref: string; count: number }>;
  pressure: {
    stale_pressure: number;
    duplicate_pressure: number;
    conflict_pressure: number;
    missing_evidence_pressure: number;
    pressure_reason_refs: string[];
  };
  token_estimate: number;
  cache_key_ref: string;
  cache_hit: boolean;
  cache_status: string;
  cache_reason_refs: string[];
  blocked_reason_refs: string[];
  safe_refs_only: boolean;
  context_injection_authorized: boolean;
  memory_write_authorized: boolean;
  semantic_search_enabled: boolean;
  vector_db_enabled: boolean;
  embedding_search_enabled: boolean;
  model_provider_authority_allowed: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryCitationIntegrityResult {
  schema_version: string;
  citation_integrity_result_ref: string;
  context_pack_ref: string;
  proposal_ref: string;
  status: string;
  valid_citation_refs: string[];
  invalid_citation_refs: string[];
  missing_source_refs: string[];
  missing_evidence_refs: string[];
  missing_receipt_refs: string[];
  orphaned_memory_refs: string[];
  orphaned_projection_refs: string[];
  unreviewed_memory_refs: string[];
  deleted_memory_refs: string[];
  superseded_memory_refs: string[];
  forget_requested_memory_refs: string[];
  blocks_context_pack_use: boolean;
  evidence_timeline_event_ref: string;
}

export interface FounderLoopMemoryCitationIntegrity {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  generated_at: string;
  proposal_count: number;
  valid_proposal_count: number;
  blocked_proposal_count: number;
  results: FounderLoopMemoryCitationIntegrityResult[];
  evidence_timeline_proof_events: Array<Record<string, unknown>>;
  citation_validation_rule_refs: string[];
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  proposal_only: boolean;
  context_injection_authorized: boolean;
  memory_write_authorized: boolean;
  truth_authority_enabled: boolean;
  model_provider_authority_allowed: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryQualityIssue {
  schema_version: string;
  issue_ref: string;
  target_ref: string;
  target_kind: string;
  issue_kind: string;
  severity: string;
  status: string;
  group_ids: string[];
  source_signal_refs: string[];
  feedback_receipt_refs: string[];
  why_queued_refs: string[];
  rank_score: number;
  proposal_only: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  delete_execution_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryQualityIssues {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  feedback_route_ref: string;
  status: string;
  generated_at: string;
  issue_count: number;
  feedback_count: number;
  groups: Array<{ group_id: string; count: number }>;
  issues: FounderLoopMemoryQualityIssue[];
  feedback_receipt_refs: string[];
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  proposal_only: boolean;
  automatic_memory_write_authorized: boolean;
  memory_write_authorized: boolean;
  delete_execution_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryMaintenanceProposal {
  schema_version: string;
  maintenance_proposal_ref: string;
  proposal_kind?: string;
  source_issue_ref?: string;
  target_ref: string;
  target_kind?: string;
  issue_kind?: string;
  severity?: string;
  rank_score: number;
  proposed_decision_kind?: string;
  reason_refs?: string[];
  source_signal_refs?: string[];
  evidence_refs?: string[];
  affected_surface_refs?: string[];
  expected_receipt_refs?: string[];
  blocked_state_refs: string[];
  next_safe_action?: string;
  proposal_only: boolean;
  auto_apply_authorized?: boolean;
  memory_write_authorized?: boolean;
  delete_execution_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_authorized?: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryMaintenanceRuns {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  run_ref: string;
  scan_ref: string;
  generated_at: string;
  proposal_count: number;
  proposals: FounderLoopMemoryMaintenanceProposal[];
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  proposal_only: boolean;
  auto_merge_authorized: boolean;
  auto_supersede_authorized: boolean;
  auto_forget_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  delete_execution_authorized: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryContextManifestItem {
  schema_version: string;
  context_manifest_ref: string;
  context_pack_ref: string;
  proposal_ref: string;
  context_pack_preview_route_ref?: string;
  context_pack_preview_status?: string;
  included_memory_refs: string[];
  excluded_memory_refs: string[];
  why_included_refs: string[];
  why_excluded_refs: string[];
  citation_integrity_status: string;
  citation_integrity_result_ref: string;
  risk_posture_ref: string;
  token_budget: number;
  token_estimate: number;
  cache_key_ref?: string;
  expires_at: string;
  safe_disable_refs: string[];
  quality_issue_refs: string[];
  blocked_state_refs: string[];
  proposal_only: boolean;
  approval_required_before_use: boolean;
  context_injection_authorized: boolean;
  hidden_prompt_context_authorized: boolean;
  runtime_prompt_context_injection_authorized?: boolean;
  live_model_context_injection_authorized?: boolean;
  automatic_context_injection_authorized: boolean;
  automatic_memory_inclusion_authorized?: boolean;
  memory_write_authorized: boolean;
  action_execution_authorized: boolean;
  connector_write_authorized: boolean;
  connector_derived_context_injection_authorized?: boolean;
  browser_web_derived_context_injection_authorized?: boolean;
  shell_file_derived_context_injection_authorized?: boolean;
  raw_payload_persistence_enabled?: boolean;
  model_provider_authority_allowed: boolean;
  provider_prompt_context_injection_authorized?: boolean;
  broad_autonomy_authorized?: boolean;
  public_beta_claim_authorized?: boolean;
  public_distribution_claim_authorized?: boolean;
  production_readiness_claim_authorized?: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryContextManifest {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  generated_at: string;
  manifest_count: number;
  manifests: FounderLoopMemoryContextManifestItem[];
  context_pack_preview_route_ref?: string;
  context_pack_preview_count?: number;
  context_pack_preview_status?: string;
  retrieval_cache_key_ref?: string;
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  proposal_only: boolean;
  context_injection_authorized: boolean;
  hidden_prompt_context_authorized: boolean;
  runtime_prompt_context_injection_authorized?: boolean;
  live_model_context_injection_authorized?: boolean;
  automatic_context_injection_authorized: boolean;
  automatic_memory_inclusion_authorized?: boolean;
  memory_write_authorized: boolean;
  action_execution_authorized: boolean;
  connector_write_authorized: boolean;
  connector_derived_context_injection_authorized?: boolean;
  browser_web_derived_context_injection_authorized?: boolean;
  shell_file_derived_context_injection_authorized?: boolean;
  raw_payload_persistence_enabled?: boolean;
  model_provider_authority_allowed: boolean;
  provider_prompt_context_injection_authorized?: boolean;
  broad_autonomy_authorized?: boolean;
  public_beta_claim_authorized?: boolean;
  public_distribution_claim_authorized?: boolean;
  production_readiness_claim_authorized?: boolean;
  production_authority_enabled: boolean;
}

export type MemoryFeedbackKind =
  | "useful"
  | "stale"
  | "missing"
  | "wrong"
  | "duplicate"
  | "conflict"
  | "irrelevant"
  | "privacy_concern";

export type MemoryFeedbackTargetKind =
  | "memory_candidate"
  | "reviewed_recall"
  | "impact_graph_node"
  | "context_pack_preview"
  | "follow_up_proposal"
  | "today_item"
  | "action_proposal"
  | "evidence_event";

export interface MemoryFeedbackRequest {
  target_ref: string;
  target_kind: MemoryFeedbackTargetKind;
  feedback_kind: MemoryFeedbackKind;
  reviewer_ref?: string;
  evidence_refs?: string[];
  reason_refs?: string[];
  metadata_refs?: string[];
  blocked_state_refs: string[];
}

export interface MemoryFeedbackReceipt {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  feedback_ref: string;
  receipt_ref: string;
  quality_issue_ref: string;
  target_ref: string;
  target_kind: MemoryFeedbackTargetKind;
  feedback_kind: MemoryFeedbackKind;
  reviewer_ref: string;
  evidence_refs: string[];
  reason_refs: string[];
  metadata_refs: string[];
  blocked_state_refs: string[];
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  status: string;
  quality_issue_created: boolean;
  memory_write_performed: boolean;
  automatic_memory_write_authorized: boolean;
  delete_execution_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_authorized: boolean;
  production_authority_enabled: boolean;
  replayed: boolean;
  created_at: string;
}

export interface FounderLoopMemoryObservationCandidate {
  observation_candidate_ref: string;
  epistemic_role: string;
  memory_kind: string;
  safe_summary: string;
  proof_count: number;
  supporting_memory_record_refs: string[];
  supporting_l2_refs: string[];
  supporting_source_refs: string[];
  supporting_evidence_refs: string[];
  supporting_receipt_refs: string[];
  duplicate_ref: string;
  conflict_ref: string;
  duplicate_candidate_refs: string[];
  conflict_candidate_refs: string[];
  freshness_refs: string[];
  score_components: Record<string, number>;
  retrieval_strategy_refs: string[];
  query_mode: string;
  safe_query_ref?: string | null;
  hrr_enabled: boolean;
  algebraic_retrieval_enabled: boolean;
}

export interface FounderLoopMemoryObservationCandidateIndex {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  query_ref?: string | null;
  safe_query_ref?: string | null;
  query_mode: string;
  candidate_count: number;
  candidates: FounderLoopMemoryObservationCandidate[];
  source_l1_preview_count: number;
  source_l2_projection_count: number;
  retrieval_strategy_refs: string[];
  search_index_status: FounderLoopMemorySearchIndexStatus;
  hrr_readiness: FounderLoopMemoryHrrReadiness;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryProbeIndex {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  entity_ref: string;
  reviewed_recall_refs: string[];
  workbench_item_refs: string[];
  l1_preview_refs: string[];
  l2_projection_refs: string[];
  l3_representation_refs: string[];
  context_pack_refs: string[];
  feedback_receipt_refs: string[];
  observation_candidate_refs: string[];
  counts: Record<string, number>;
  search_index_status: FounderLoopMemorySearchIndexStatus;
  hrr_readiness: FounderLoopMemoryHrrReadiness;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryContradictionPreview {
  contradiction_preview_ref: string;
  memory_ref: string;
  duplicate_key_ref: string;
  conflict_key_ref: string;
  stale_state_ref: string;
  reason_refs: string[];
  supporting_source_refs: string[];
  supporting_evidence_refs: string[];
  supporting_receipt_refs: string[];
  safe_summary: string;
  hrr_enabled: boolean;
  algebraic_retrieval_enabled: boolean;
}

export interface FounderLoopMemoryContradictionPreviewIndex {
  schema_version: string;
  contract_ref: string;
  route_ref: string;
  status: string;
  preview_count: number;
  previews: FounderLoopMemoryContradictionPreview[];
  ranking_contract_ref: string;
  search_index_status: FounderLoopMemorySearchIndexStatus;
  hrr_readiness: FounderLoopMemoryHrrReadiness;
  blocked_state_refs: string[];
}

export interface FounderLoopMemoryContextPackActionProposalRequest {
  decision_reason_ref: string;
  metadata_refs?: string[];
  exact_approval_scope_ref?: string | null;
  approval_ref?: string | null;
}

export interface FounderLoopMemoryContextPackActionProposalReceipt {
  contract_ref: string;
  route_ref: string;
  status: string;
  context_pack_ref: string;
  context_pack_proposal_ref: string;
  internal_action_proposal_ref: string;
  item_ref: string;
  action_envelope_ref: string;
  exact_approval_scope_ref: string;
  approval_ref: string;
  approval_status: string;
  approval_reason_refs: string[];
  receipt_ref: string;
  audit_ref: string;
  idempotency_key_ref: string;
  payload_fingerprint_ref: string;
  evidence_timeline_event_ref: string;
  source_memory_record_refs: string[];
  l1_preview_refs: string[];
  l2_projection_refs: string[];
  l3_representation_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  supporting_receipt_refs: string[];
  rollback_ref: string;
  safe_disable_ref: string;
  blocked_state_refs: string[];
  action_proposal_created: boolean;
  action_executed: boolean;
  approval_grants_execution: boolean;
  connector_write_performed: boolean;
  crm_sync_performed: boolean;
  account_sync_performed: boolean;
  shell_subprocess_performed: boolean;
  browser_automation_performed: boolean;
  provider_model_call_performed: boolean;
  context_injection_performed: boolean;
  memory_write_performed: boolean;
  raw_content_stored: boolean;
  replayed: boolean;
  safe_summary: string;
  created_at: string;
}

export interface FounderLoopMemoryContextPacks {
  contract_ref: string;
  route_ref: string;
  status: string;
  query_ref?: string | null;
  generated_at?: string;
  source_l1_contract_ref?: string;
  source_l2_contract_ref?: string;
  source_l3_contract_ref?: string;
  source_l1_preview_count: number;
  source_l2_projection_count: number;
  source_l3_representation_count: number;
  context_pack_count: number;
  proposals: FounderLoopMemoryContextPackProposal[];
  skipped_ref_reasons?: string[];
  internal_action_proposal_receipts?: unknown[];
  phase6_1_internal_action_proposal_status?: string;
  blocked_state_refs: string[];
  safe_refs_only: boolean;
  proposal_only: boolean;
  derived_from_reviewed_memory_only: boolean;
  context_injection_authorized: boolean;
  hidden_prompt_context_authorized: boolean;
  automatic_context_injection_authorized: boolean;
  prompt_context_written: boolean;
  truth_authority_enabled: boolean;
  approval_authority_granted: boolean;
  connector_write_authorized: boolean;
  external_crm_sync_authorized: boolean;
  account_sync_authorized: boolean;
  automatic_action_execution_authorized: boolean;
  model_provider_authority_allowed: boolean;
  production_authority_enabled: boolean;
  embedding_index_enabled: boolean;
  vector_db_enabled: boolean;
  semantic_search_enabled: boolean;
  background_indexing_enabled: boolean;
  phase6_execution_hooks_enabled: boolean;
  raw_content_stored: boolean;
  context_injection_performed: boolean;
  provider_model_call_performed: boolean;
}

export interface FounderLoopWeeklyCeoReviewSummary {
  weekly_review_ref: string;
  input_refs: string[];
  decision_refs: string[];
  commitment_refs: string[];
  carry_forward_task_refs: string[];
  unresolved_blocker_refs: string[];
  memory_correction_refs: string[];
  rejected_item_refs: string[];
  stale_memory_refs: string[];
  missing_evidence_blocker_refs: string[];
  follow_up_opportunity_refs: string[];
  authority_boundary: string;
  next_safe_action: string;
}

export type FounderLoopSourceReadinessStatus =
  | "ready"
  | "blocked"
  | "missing"
  | "metadata_only"
  | "unavailable"
  | "not_configured";

export interface FounderLoopSourceReadinessItem {
  source_ref: string;
  source_kind: string;
  status: FounderLoopSourceReadinessStatus;
  safe_summary: string;
  next_safe_action: string;
  source_refs: string[];
  evidence_refs: string[];
  blocked_state_refs: string[];
  authority_boundary: string;
}

export interface FounderLoopSourceReadinessPosture {
  schema_version: "founder_loop_source_readiness_posture.v1";
  source: string;
  backend_owned: boolean;
  status: string;
  source_count: number;
  ready_source_count: number;
  blocked_source_count: number;
  metadata_only_source_count: number;
  not_configured_source_count: number;
  supported_statuses: FounderLoopSourceReadinessStatus[];
  missing_contract_refs: string[];
  blocked_state_refs: string[];
  blocked_authority_refs?: string[];
  connector_runtime_enabled: boolean;
  source_refresh_enabled: boolean;
  notification_delivery_enabled: boolean;
  account_auth_enabled?: boolean;
  raw_source_ingestion_enabled?: boolean;
  write_authority_enabled?: boolean;
  authority_boundary: string;
  next_safe_action: string;
}

export interface FounderLoopSourceReadinessProposalCandidate {
  schema_version: "founder_loop_source_readiness_proposal.v1";
  source: string;
  backend_owned: boolean;
  proposal_ref: string;
  action_item_ref: string;
  title: string;
  safe_summary: string;
  surface: string;
  source_kind: string;
  source_readiness_ref: string;
  source_readiness_route_ref: string;
  missing_contract_ref: string;
  proposal_kind: string;
  proposal_classification: "proposal_only_no_execution_path";
  action_kind: string;
  status: string;
  side_effect_class: string;
  risk_class: string;
  approval_required: boolean;
  local_task_commit_eligible: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  source_refresh_enabled: boolean;
  raw_source_ingestion_enabled: boolean;
  write_authority_enabled: boolean;
  blocked_authority_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
}

export interface ConnectorDraftProposalItem {
  schema_version: "connector_draft_proposal_item.v1";
  proposal_ref: string;
  draft_ref: string;
  draft_kind: "email_response" | "calendar_event_hold";
  source_kind: "email" | "calendar";
  status: "draft_proposal_ready";
  connector_ref: string;
  channel_ref: string;
  target_session_ref: string;
  delivery_ref: string;
  delivery_state: "draft_created_metadata_only";
  delivery_event_ref: string;
  source_metadata_refs: string[];
  redacted_subject_ref: string;
  redacted_body_summary_ref: string;
  draft_summary_ref: string;
  response_outline_ref: string;
  outbound_approval_ref: string;
  approval_posture_ref: string;
  approval_posture: string;
  idempotency_ref: string;
  rollback_posture_ref: string;
  safe_disable_posture_ref: string;
  audit_ref: string;
  replay_ref: string;
  evidence_refs: string[];
  proof_refs: string[];
  blocked_send_write_reason_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
  redacted_outline: string[];
  next_safe_action: string;
  safe_refs_only: boolean;
  draft_only: boolean;
  metadata_only: boolean;
  approval_required_to_draft: boolean;
  approval_required_to_send: boolean;
  outbound_approval_ref_grants_authority: boolean;
  target_session_ref_grants_authority: boolean;
  raw_payloads_persisted: boolean;
  raw_body_persisted: boolean;
  raw_content_persisted: boolean;
  raw_draft_body_persisted: boolean;
  contact_data_persisted: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  oauth_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  connector_delete_enabled: boolean;
  connector_delivery_worker_enabled: boolean;
  background_sync_enabled: boolean;
  scheduler_enabled: boolean;
  provider_model_calls_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_enabled: boolean;
  delivery_execution_performed: boolean;
  connector_write_performed: boolean;
  connector_send_performed: boolean;
  account_sync_performed: boolean;
  production_authority_enabled: boolean;
}

export interface ConnectorDraftProposalReadModel {
  schema_version: "connector_draft_proposal_read_model.v1";
  source: string;
  backend_owned: boolean;
  status: "draft_proposals_ready_no_send_write";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  proposal_count: number;
  proposals: ConnectorDraftProposalItem[];
  evidence_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  draft_only: boolean;
  metadata_only: boolean;
  raw_payloads_persisted: boolean;
  connector_runtime_enabled: boolean;
  account_auth_enabled: boolean;
  oauth_enabled: boolean;
  connector_writes_enabled: boolean;
  connector_sends_enabled: boolean;
  background_sync_enabled: boolean;
  scheduler_enabled: boolean;
  provider_model_calls_enabled: boolean;
  memory_write_enabled: boolean;
  context_injection_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopSourceReadiness {
  schema_version: "founder_loop_source_readiness.v1";
  source: string;
  backend_owned: boolean;
  generated_at: string;
  status: string;
  surface: string;
  route_ref: string;
  route_refs: string[];
  source_readiness_items: FounderLoopSourceReadinessItem[];
  source_readiness_posture: FounderLoopSourceReadinessPosture;
  source_readiness_proposal_candidates: FounderLoopSourceReadinessProposalCandidate[];
  connector_draft_proposals?: ConnectorDraftProposalReadModel;
  supported_statuses: FounderLoopSourceReadinessStatus[];
  missing_contract_refs: string[];
  blocked_state_refs: string[];
  blocked_authority_refs: string[];
  evidence_refs: string[];
  connector_runtime_enabled: boolean;
  source_refresh_enabled: boolean;
  notification_delivery_enabled: boolean;
  account_auth_enabled: boolean;
  raw_source_ingestion_enabled: boolean;
  write_authority_enabled: boolean;
  connector_draft_proposals_enabled?: boolean;
  authority_boundary: string;
  next_safe_action: string;
}

export interface FounderLoopCrmLiteFollowUp {
  contract_ref: string;
  follow_up_ref: string;
  relationship_ref: string;
  person_ref: string;
  org_ref: string;
  project_ref: string;
  opportunity_ref: string;
  promise_ref: string;
  status: string;
  relationship_memory_posture: string;
  redaction_status: string;
  safe_summary: string;
  why_now: string;
  draft_available: boolean;
  review_envelope_ref: string;
  memory_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  blocked_state_refs: string[];
  authority_boundary: string;
  review_required_before_action: boolean;
  safe_refs_only: boolean;
  crm_sync_enabled: boolean;
  crm_write_enabled: boolean;
  external_write_enabled: boolean;
  connector_read_authorized: boolean;
  connector_write_authorized: boolean;
  account_sync_authorized: boolean;
  email_calendar_fetch_authorized: boolean;
  context_injection_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  action_execution_authorized: boolean;
  model_provider_call_authorized: boolean;
  production_authority_enabled: boolean;
}

export type FounderLoopFollowUpTrackerCategory =
  | "relationship_follow_up"
  | "promise"
  | "open_loop"
  | "pending_reply"
  | "deferred_decision";

export interface FounderLoopFollowUpTrackerItem {
  item_ref: string;
  category: FounderLoopFollowUpTrackerCategory;
  title: string;
  status: string;
  source_state: string;
  safe_summary: string;
  why_shown: string;
  relationship_ref?: string | null;
  promise_ref?: string | null;
  opportunity_ref?: string | null;
  action_ref?: string | null;
  memory_refs: string[];
  source_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  blocked_state_refs: string[];
  stale_state?: string | null;
  next_safe_action: string;
  authority_boundary: string;
  review_required: boolean;
  local_review_only: boolean;
  safe_refs_only: boolean;
  no_source_state: boolean;
  reminder_scheduler_enabled: boolean;
  message_send_enabled: boolean;
  connector_read_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_fetch_enabled: boolean;
  automatic_task_creation_enabled: boolean;
  action_execution_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  context_injection_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopFollowUpTrackerReadModel {
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  category_order: FounderLoopFollowUpTrackerCategory[];
  items: FounderLoopFollowUpTrackerItem[];
  relationship_follow_up_refs: string[];
  promise_refs: string[];
  open_loop_refs: string[];
  pending_reply_refs: string[];
  deferred_decision_refs: string[];
  stale_refs: string[];
  no_source_refs: string[];
  blocked_state_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  reminder_scheduler_enabled: boolean;
  message_send_enabled: boolean;
  connector_read_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_fetch_enabled: boolean;
  automatic_task_creation_enabled: boolean;
  action_execution_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  context_injection_authorized: boolean;
  hidden_memory_write_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopMemoryWhyShownItem {
  memory_ref: string;
  loop_item_ref: string;
  surface: string;
  why_shown: string;
  review_state: string;
  stale_state: string;
  conflict_state: string;
  source_refs: string[];
  evidence_refs: string[];
  missing_evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  reviewed_recall_only: boolean;
  context_injection_authorized: boolean;
  memory_truth_authority: boolean;
}

export interface FounderLoopReviewQueueGroup {
  group_ref: string;
  kind: string;
  count: number;
  status: string;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  blocked_state_refs: string[];
}

export interface FounderLoopDogfoodCaptureSummary {
  capture_ref: string;
  status: string;
  safe_summary: string;
  capture_event_kinds: string[];
  metric_refs: string[];
  review_item_refs: string[];
  friction_refs: string[];
  recommendation_candidate_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  local_private_only: boolean;
  safe_refs_only: boolean;
  public_beta_claim_enabled: boolean;
  production_readiness_claim_enabled: boolean;
  public_distribution_enabled: boolean;
  action_execution_enabled: boolean;
  auto_apply_enabled: boolean;
}

export interface FounderLoopWeeklyReviewNarrative {
  weekly_review_ref: string;
  status: string;
  safe_summary: string;
  proposed_refs: string[];
  decided_refs: string[];
  changed_refs: string[];
  completed_refs?: string[];
  deferred_refs?: string[];
  rejected_refs?: string[];
  planned_refs?: string[];
  memory_change_refs?: string[];
  crm_movement_refs?: string[];
  draft_refs?: string[];
  next_week_priority_refs?: string[];
  carry_forward_refs: string[];
  blocked_refs: string[];
  stale_refs: string[];
  missing_source_refs: string[];
  dogfood_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
}

export interface FounderLoopWeeklyCeoReviewV1ReadModel {
  schema_version: "product-loop-008-weekly-ceo-review.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_review_artifact_only: boolean;
  safe_refs_only: boolean;
  safe_summary_only: boolean;
  raw_content_included: boolean;
  evidence_backed: boolean;
  review_period_ref: string;
  safe_summary: string;
  completed_count: number;
  deferred_count: number;
  rejected_count: number;
  blocked_count: number;
  stale_count: number;
  unresolved_count: number;
  action_decision_count: number;
  memory_decision_count: number;
  follow_up_count: number;
  evidence_event_count: number;
  completed_refs: string[];
  deferred_refs: string[];
  rejected_refs: string[];
  blocked_refs: string[];
  stale_refs: string[];
  unresolved_refs: string[];
  carry_forward_refs: string[];
  next_week_priority_refs: string[];
  action_decision_refs: string[];
  memory_decision_refs: string[];
  follow_up_refs: string[];
  evidence_event_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  missing_source_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  raw_logs_included: boolean;
  prompt_content_included: boolean;
  response_content_included: boolean;
  provider_exchange_content_included: boolean;
  connector_read_enabled: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_fetch_enabled: boolean;
  live_web_enabled: boolean;
  model_summary_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  public_beta_claim_enabled: boolean;
  production_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export type FounderLoopProductProofStepId =
  | "morning_briefing"
  | "today"
  | "action_inbox"
  | "decision_receipt"
  | "evidence_timeline"
  | "memory_review"
  | "weekly_review";

export interface FounderLoopProductProofStep {
  step_id: FounderLoopProductProofStepId;
  surface: string;
  backend_route_ref: string;
  frontend_route_ref: string;
  status: string;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
}

export type FounderLoopProductizedSurfaceId =
  | "start_here"
  | "today"
  | "action_inbox"
  | "proof"
  | "evidence"
  | "memory"
  | "trust"
  | "settings";

export interface FounderLoopProductizedSurfaceBinding {
  surface_id: FounderLoopProductizedSurfaceId;
  surface: string;
  frontend_route_ref: string;
  backend_route_ref: string;
  status: string;
  product_posture: string;
  safe_summary: string;
  shared_ref: string;
  primary_proof_ref: string;
  source_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  memory_candidate_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopProductProofReadModel {
  schema_version: "founder-loop-v1-product-proof.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  seeded_demo_safe: boolean;
  safe_refs_only: boolean;
  safe_summary_only: boolean;
  raw_content_included: boolean;
  scenario_ref: string;
  shared_state_ref: string;
  full_strength_goal: string;
  repo_safe_scope: string;
  blocked_authority_summary: string;
  exact_promotion_path_refs: string[];
  productized_surface_order: FounderLoopProductizedSurfaceId[];
  productized_surface_count: number;
  productized_surface_bindings: FounderLoopProductizedSurfaceBinding[];
  productized_route_refs: string[];
  productized_backend_route_refs: string[];
  loop_order: FounderLoopProductProofStepId[];
  steps: FounderLoopProductProofStep[];
  supported_decision_actions: string[];
  morning_briefing_refs: string[];
  today_refs: string[];
  action_inbox_refs: string[];
  action_decision_receipt_refs: string[];
  evidence_timeline_refs: string[];
  evidence_event_refs: string[];
  memory_review_candidate_refs: string[];
  memory_review_receipt_refs: string[];
  weekly_review_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  memory_review_status: "candidate_available" | "none";
  weekly_review_status: string;
  decision_receipt_status: string;
  safe_summary: string;
  next_safe_action: string;
  authority_boundary: string;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  a2a_runtime_dispatch_enabled: boolean;
  mcp_runtime_dispatch_enabled: boolean;
  browser_execution_enabled: boolean;
  live_web_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_send_enabled: boolean;
  crm_write_enabled: boolean;
  account_sync_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  public_beta_claim_enabled: boolean;
  public_release_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopTraceRefs {
  run_refs: string[];
  operator_run_event_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  evidence_event_refs: string[];
  proof_refs: string[];
  approval_refs: string[];
  blocked_authority_refs: string[];
}

export type FounderLoopRunsIntegrationSurfaceId =
  | "morning_briefing"
  | "today"
  | "action_inbox"
  | "decision_receipt"
  | "evidence_timeline"
  | "memory_review"
  | "weekly_review";

export interface FounderLoopRunsIntegrationSurfaceBinding {
  surface_id: FounderLoopRunsIntegrationSurfaceId;
  surface: string;
  status: string;
  frontend_route_ref: string;
  backend_route_ref: string;
  run_ref: string;
  proof_ref: string;
  proof_detail_ref: string;
  proof_detail_route_ref: string;
  action_source_refs: string[];
  approval_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  evidence_event_refs?: string[];
  memory_candidate_refs: string[];
  operator_run_event_refs: string[];
  blocked_state_refs: string[];
  safe_summary: string;
  next_safe_action: string;
}

export interface FounderLoopRunsIntegrationReadModel {
  schema_version: "founder-loop-runs-integration.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  raw_payloads_persisted: boolean;
  ui_truth_source: string;
  primary_run_ref: string;
  primary_proof_ref: string;
  surface_order: FounderLoopRunsIntegrationSurfaceId[];
  surface_count: number;
  run_refs: string[];
  proof_refs: string[];
  proof_detail_refs: string[];
  action_source_refs: string[];
  approval_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  evidence_event_refs: string[];
  memory_candidate_refs: string[];
  operator_run_event_refs: string[];
  blocked_authority_refs: string[];
  surface_bindings: FounderLoopRunsIntegrationSurfaceBinding[];
  action_origin_posture: string;
  decision_receipt_posture: string;
  evidence_path_posture: string;
  proof_detail_posture: string;
  memory_candidate_posture: string;
  weekly_review_posture: string;
  authority_boundary: string;
  next_safe_action: string;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  browser_execution_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  scheduler_enabled: boolean;
  background_autonomy_enabled: boolean;
  action_execution_enabled: boolean;
  approval_authority_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  ui_mutation_authority_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ControlCenterStartHereStep {
  step_id: string;
  label: string;
  route_ref: string;
  backend_route_ref: string;
  status: string;
  safe_summary: string;
  next_safe_action: string;
  run_ref: string;
  proof_ref: string;
  receipt_refs: string[];
  evidence_refs: string[];
  approval_refs: string[];
  memory_candidate_refs: string[];
  blocked_authority_refs: string[];
}

export interface ControlCenterStartHereSummary {
  schema_version: "control-center-start-here-summary.v1";
  contract_ref: string;
  status: string;
  readiness_state: string;
  local_loop_status: string;
  source:
    | "python_core_control_center_start_here_read_model"
    | "mock_fallback_non_authoritative";
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  redacted_summaries_only: boolean;
  raw_content_included: boolean;
  ui_truth_source: string;
  primary_run_ref: string;
  primary_proof_ref: string;
  action_proposal_ref: string;
  route_refs: string[];
  backend_route_refs: string[];
  steps: ControlCenterStartHereStep[];
  complete_daily_loop_available: boolean;
  operator_goal: string;
  next_safe_action: string;
  missing_prerequisite_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  browser_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export type ControlCenterProofKind =
  | "daily_loop"
  | "action_decision"
  | "local_task_commit"
  | "memory_decision"
  | "evidence_event"
  | "web_evidence"
  | "provider_draft_preview"
  | "connector_draft_proposal"
  | "operator_workspace_spine"
  | "source_readiness"
  | "approval"
  | "setup_package";

export interface ControlCenterProofRunDetail {
  schema_version: "control-center-proof-run-detail.v1";
  contract_ref: string;
  source:
    | "python_core_control_center_proof_run_detail"
    | "mock_control_center_proof_run_detail_non_authoritative";
  run_detail_ref: string;
  proof_ref: string;
  proof_kind: ControlCenterProofKind;
  run_ref: string;
  status: string;
  title: string;
  safe_summary: string;
  authority_posture: string;
  full_strength_goal: string;
  repo_safe_scope: string;
  blocked_authority_summary: string;
  exact_promotion_path_refs: string[];
  route_refs: string[];
  backend_route_refs: string[];
  cli_ref: string;
  related_run_refs: string[];
  operator_run_event_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  audit_refs: string[];
  approval_refs: string[];
  rollback_refs: string[];
  safe_disable_refs: string[];
  memory_candidate_refs: string[];
  blocked_authority_refs: string[];
  redaction_state: string;
  next_safe_action: string;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  control_center_presentation_only: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  browser_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ControlCenterProofRecord {
  schema_version: "control-center-proof-record.v1";
  contract_ref: string;
  proof_ref: string;
  proof_kind: ControlCenterProofKind;
  status: string;
  title: string;
  safe_summary: string;
  authority_posture: string;
  route_refs: string[];
  backend_route_refs: string[];
  run_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  audit_refs: string[];
  approval_refs: string[];
  rollback_refs: string[];
  safe_disable_refs: string[];
  memory_candidate_refs: string[];
  redaction_state: string;
  next_safe_action: string;
  blocked_authority_refs: string[];
  detail_route_ref: string;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  control_center_presentation_only: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  browser_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
  run_detail: ControlCenterProofRunDetail | null;
}

export interface ControlCenterProofIndex {
  schema_version: "control-center-proof-index.v1";
  contract_ref: string;
  source:
    | "python_core_control_center_proof_index"
    | "mock_fallback_non_authoritative";
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  index_route_ref: string;
  detail_route_ref: string;
  cli_ref: string;
  proof_count: number;
  proof_refs: string[];
  records: ControlCenterProofRecord[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  connector_write_enabled: boolean;
  connector_send_enabled: boolean;
  browser_execution_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface WebEvidenceProductSliceRequest {
  request_ref: string;
  url: string;
  allowed_host: string;
  attach_to_ref?: string;
  safe_summary?: string;
  evidence_refs?: string[];
  metadata_refs?: string[];
}

export interface WebEvidenceProductSliceReceipt {
  schema_version: "control-center-web-evidence-product-slice-receipt.v1";
  contract_ref: string;
  source: "python_core_web_evidence_product_slice";
  status: string;
  route_ref: "POST /control-center/web-evidence/attach";
  cli_ref: string;
  request_ref: string;
  attach_to_ref: string;
  attachment_ref: string;
  receipt_ref: string;
  evidence_ref: string;
  proof_ref: string;
  preview_ref: string;
  safe_url_ref: string;
  host_ref: string;
  transport_ref: string;
  web_access_request_ref: string;
  web_access_audit_ref: string;
  web_access_audit_summary: {
    schema_version: "web-access-audit-summary.v1";
    request_ref: string;
    safe_url_ref: string;
    host_ref: string;
    timestamp: string;
    adapter_kind: string;
    network_lane: string;
    authority_mode: string;
    risk_class: string;
    policy_status: string;
    policy_reason_refs: string[];
    source_metadata_refs: string[];
    content_untrusted: boolean;
    raw_url_omitted: boolean;
    raw_headers_omitted: boolean;
    raw_body_omitted: boolean;
  };
  payload_fingerprint_ref: string;
  status_code: number;
  content_type: string;
  redacted_preview: string;
  preview_truncated: boolean;
  preview_limit_bytes: number;
  response_bytes_read: number;
  redaction_count: number;
  redaction_posture_ref: string;
  receipt_refs: string[];
  evidence_refs: string[];
  audit_refs: string[];
  rollback_refs: string[];
  safe_disable_refs: string[];
  blocked_authority_refs: string[];
  authority_posture: string;
  next_safe_action: string;
  safe_refs_only_for_durable_surfaces: boolean;
  redacted_preview_returned_to_requester: boolean;
  web_access_gateway_required: boolean;
  configured_host_allowlist_required: boolean;
  operator_supplied_host_scope_required: boolean;
  request_ref_payload_idempotency: boolean;
  request_ref_idempotency_ref: string;
  raw_response_body_stored: boolean;
  raw_headers_stored: boolean;
  absolute_url_returned: boolean;
  query_string_returned: boolean;
  auth_session_state_used: boolean;
  request_body_sent: boolean;
  non_get_method_used: boolean;
  redirect_followed: boolean;
  download_performed: boolean;
  browser_automation_performed: boolean;
  context_injection_performed: boolean;
  memory_write_performed: boolean;
  model_call_performed: boolean;
  connector_write_performed: boolean;
  action_execution_performed: boolean;
  production_authority_granted: boolean;
  replayed: boolean;
  durable_record_ref?: string;
}

export type FounderLoopUnifiedWorkThreadStepId =
  | "chat_handoff"
  | "plan"
  | "action"
  | "decision_receipt"
  | "evidence"
  | "memory_review"
  | "weekly_review";

export interface FounderLoopUnifiedWorkThreadStep {
  step_id: FounderLoopUnifiedWorkThreadStepId;
  surface: string;
  frontend_route_ref: string;
  backend_route_ref: string;
  status: string;
  safe_summary: string;
  source_refs: string[];
  proposal_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopUnifiedWorkThreadReadModel {
  schema_version: "fcc-thread-001-unified-work-thread.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  seeded_demo_safe: boolean;
  safe_refs_only: boolean;
  safe_summary_only: boolean;
  raw_content_included: boolean;
  thread_ref: string;
  thread_title: string;
  step_order: FounderLoopUnifiedWorkThreadStepId[];
  steps: FounderLoopUnifiedWorkThreadStep[];
  chat_turn_receipt_refs: string[];
  chat_handoff_receipt_refs: string[];
  plan_refs: string[];
  plan_proposal_refs: string[];
  action_refs: string[];
  action_decision_receipt_refs: string[];
  evidence_timeline_refs: string[];
  evidence_event_refs: string[];
  memory_review_candidate_refs: string[];
  memory_review_receipt_refs: string[];
  weekly_review_refs: string[];
  receipt_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
  next_safe_action: string;
  authority_boundary: string;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  a2a_runtime_dispatch_enabled: boolean;
  mcp_runtime_dispatch_enabled: boolean;
  browser_execution_enabled: boolean;
  live_web_enabled: boolean;
  connector_read_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_send_enabled: boolean;
  crm_write_enabled: boolean;
  account_sync_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_enabled: boolean;
  public_beta_claim_enabled: boolean;
  public_release_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export type FounderLoopChatToLoopOutcomeKind =
  | "remember_this"
  | "create_action"
  | "add_to_plan"
  | "defer"
  | "ask_human"
  | "blocked";

export interface FounderLoopChatToLoopHandoffOutcome {
  outcome_ref: string;
  outcome_kind: FounderLoopChatToLoopOutcomeKind;
  state: string;
  target_surface: "Memory" | "Actions" | "Plans" | "Chat" | "Authority";
  safe_label: string;
  source_ref: string;
  proposal_ref: string;
  receipt_refs: string[];
  evidence_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopChatToLoopHandoffReadModel {
  schema_version: "product-loop-009-chat-to-loop-handoff.v1";
  contract_ref: string;
  source: string;
  status: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  proposal_only: boolean;
  safe_refs_only: boolean;
  safe_summary_only: boolean;
  raw_content_included: boolean;
  idempotency_bound: boolean;
  outcome_kinds: FounderLoopChatToLoopOutcomeKind[];
  safe_summary: string;
  outcome_count: number;
  turn_receipt_count: number;
  handoff_receipt_count: number;
  remember_this_count: number;
  create_action_count: number;
  add_to_plan_count: number;
  defer_count: number;
  ask_human_count: number;
  blocked_count: number;
  outcomes: FounderLoopChatToLoopHandoffOutcome[];
  outcome_refs: string[];
  turn_receipt_refs: string[];
  handoff_receipt_refs: string[];
  action_created_refs: string[];
  plan_created_refs: string[];
  memory_proposal_refs: string[];
  defer_refs: string[];
  ask_human_refs: string[];
  evidence_refs: string[];
  idempotency_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  model_output_authority: boolean;
  direct_memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  tool_execution_enabled: boolean;
  connector_write_enabled: boolean;
  action_execution_enabled: boolean;
  plan_execution_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  live_web_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopDailyLoopSummary {
  loop_ref: string;
  status: string;
  home_surface: string;
  decision_surface: string;
  safe_summary: string;
  today_plan_summary: string;
  review_queue_summary: string;
  source_readiness_state_refs: string[];
  crm_follow_up_refs: string[];
  memory_reason_refs: string[];
  review_group_refs: string[];
  weekly_review_ref: string;
  dogfood_capture_ref: string;
  next_safe_action: string;
  authority_boundary: string;
  action_execution_enabled: boolean;
  connector_runtime_enabled: boolean;
  external_write_enabled: boolean;
  runtime_model_calls_enabled: boolean;
}

export interface FounderLoopBriefingSection {
  section_ref: string;
  title: string;
  status: string;
  safe_summary: string;
  source_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  blocked_state_refs: string[];
}

export interface FounderLoopPrivateBetaReadinessCriterion {
  contract_ref: string;
  criterion_ref: string;
  surface: string;
  gate_state: string;
  safe_summary: string;
  evidence_refs: string[];
  required_contract_refs: string[];
  acceptance_refs: string[];
  missing_evidence_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  local_private_only: boolean;
  safe_refs_only: boolean;
  review_required: boolean;
  evidence_required: boolean;
  redaction_required: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_readiness_claim_enabled: boolean;
  production_authority_enabled: boolean;
  broad_autonomy_enabled: boolean;
  connector_write_enabled: boolean;
  provider_model_authority_allowed: boolean;
  unrestricted_shell_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  remote_execution_enabled: boolean;
  account_sync_enabled: boolean;
  crm_write_enabled: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  code_apply_execution_enabled: boolean;
}

export interface FounderLoopPrivateBetaReadinessStateDefinition {
  state: string;
  terminal: boolean;
  definition: string;
}

export interface FounderLoopPrivateBetaReadinessSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopPrivateBetaReadinessAuthorityPosture {
  local_private_only: boolean;
  safe_refs_only: boolean;
  review_required: boolean;
  evidence_required: boolean;
  redaction_required: boolean;
  private_beta_execution_authorized: boolean;
  public_beta_claim_enabled: boolean;
  public_distribution_claim_enabled: boolean;
  production_readiness_claim_enabled: boolean;
  production_authority_enabled: boolean;
  broad_autonomy_enabled: boolean;
  connector_write_enabled: boolean;
  provider_model_authority_allowed: boolean;
  unrestricted_shell_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  remote_execution_enabled: boolean;
  account_sync_enabled: boolean;
  crm_write_enabled: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  approval_grant_capture_enabled: boolean;
  action_execution_enabled: boolean;
  code_apply_execution_enabled: boolean;
}

export interface FounderLoopUserIntentProposal {
  contract_ref: string;
  proposal_ref: string;
  source_surface: string;
  intent_label: string;
  safe_summary: string;
  confidence_score: number;
  confidence_band: string;
  ambiguity_posture: string;
  routing_decision: string;
  route_ref: string;
  source_refs: string[];
  evidence_refs: string[];
  dependency_refs: string[];
  required_contract_refs: string[];
  conflict_refs: string[];
  ask_user_question_ref?: string | null;
  next_safe_action: string;
  review_required: boolean;
  safe_refs_only: boolean;
  evidence_required: boolean;
  low_confidence_asks_user: boolean;
  conflicting_intent_asks_user: boolean;
  hidden_authority_enabled: boolean;
  acts_without_review: boolean;
  action_execution_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  tool_execution_enabled: boolean;
  provider_model_authority_allowed: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  code_apply_execution_enabled: boolean;
  broad_autonomy_enabled: boolean;
  public_beta_claim_enabled: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopUserIntentSurfaceBinding {
  surface: string;
  feed_status: string;
  feed_ref: string;
  authority_boundary: string;
}

export interface FounderLoopUserIntentAuthorityPosture {
  review_required: boolean;
  safe_refs_only: boolean;
  evidence_required: boolean;
  low_confidence_asks_user: boolean;
  conflicting_intent_asks_user: boolean;
  hidden_authority_enabled: boolean;
  acts_without_review: boolean;
  action_execution_enabled: boolean;
  approval_grant_capture_enabled: boolean;
  memory_write_authorized: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  tool_execution_enabled: boolean;
  provider_model_authority_allowed: boolean;
  connector_write_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  code_apply_execution_enabled: boolean;
  broad_autonomy_enabled: boolean;
  public_beta_claim_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopTodaySignal {
  signal: string;
  source: string;
  required: boolean;
}

export interface FounderLoopModuleFeedContract {
  module: string;
  status: string;
  required_loop_outputs: string[];
  current_feed_refs: string[];
  standalone_complete_allowed: boolean;
}

export interface FounderLoopModuleCompletionContract {
  visibility_requirement: string;
  visibility_is_sufficient_for_completion: boolean;
  standalone_module_complete_allowed: boolean;
  required_done_gates: string[];
}

export interface FounderLoopNextSafeAction {
  surface: string;
  source_ref: string;
  safe_summary: string;
}

export interface FounderLoopPlanActionState {
  action_count: number;
  plan_count: number;
  approval_required_before_mutation: boolean;
  mutating_controls_enabled: boolean;
  execution_authorized: boolean;
  action_envelope_contract_status: string;
  action_envelope_contract_ref?: string;
  review_actions?: string[];
  approval_grant_capture_enabled?: boolean;
  state_change_enabled?: boolean;
  vertical_slice_contract_ref?: string;
  today_action_envelope_route_refs?: string[];
}

export interface FounderLoopStaleSourcePosture {
  status: string;
  source_refresh_enabled: boolean;
  connector_runtime_enabled: boolean;
  stale_state_refs: string[];
}

export type FounderLoopTodayLoopLaneId =
  | "needs_review"
  | "blocked_now"
  | "changed"
  | "follow_up"
  | "stale_or_deferred";

export interface FounderLoopTodayLoopDigestItem {
  item_ref: string;
  lane_id: FounderLoopTodayLoopLaneId;
  surface: string;
  title: string;
  state_label: string;
  status: string;
  priority: string;
  safe_summary: string;
  reason: string;
  source_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  blocked_state_refs: string[];
  stale_state?: string | null;
  review_required: boolean;
  next_safe_action: string;
  authority_boundary: string;
  safe_refs_only: boolean;
  content_untrusted: boolean;
  action_execution_enabled: boolean;
  connector_runtime_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
}

export interface FounderLoopTodayLoopLane {
  lane_id: FounderLoopTodayLoopLaneId;
  label: string;
  status: string;
  count: number;
  item_refs: string[];
  evidence_refs: string[];
  receipt_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  review_only: boolean;
}

export interface FounderLoopTodayLoopReadModel {
  schema_version: string;
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  lane_order: FounderLoopTodayLoopLaneId[];
  lanes: FounderLoopTodayLoopLane[];
  digest_items: FounderLoopTodayLoopDigestItem[];
  what_matters_now_refs: string[];
  what_changed_refs: string[];
  blocked_now_refs: string[];
  needs_review_refs: string[];
  follow_up_refs: string[];
  stale_or_deferred_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  action_execution_enabled: boolean;
  connector_runtime_enabled: boolean;
  source_refresh_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  automatic_memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
  blocked_state_refs: string[];
}

export interface FounderLoopAgentLoopFact {
  fact_ref: string;
  summary: string;
  evidence_refs: string[];
}

export interface FounderLoopAgentLoopReviewItem {
  assumption_ref?: string;
  unknown_ref?: string;
  summary: string;
  review_required?: boolean;
  blocked_state_refs?: string[];
}

export interface FounderLoopAgentLoopPlanStep {
  step_ref: string;
  title: string;
  status: string;
  evidence_refs: string[];
  blocked_state_refs: string[];
  execution_enabled: boolean;
}

export interface FounderLoopAgentLoopProposedAction {
  action_ref: string;
  title: string;
  status: string;
  action_kind: string;
  approval_required: boolean;
  approval_envelope_ref: string;
  state_change_readiness: string;
  execution_enabled: boolean;
  receipt_refs: string[];
  evidence_refs: string[];
  next_safe_action: string;
}

export interface FounderLoopAgentLoopThread {
  schema_version: string;
  contract_ref: string;
  thread_ref: string;
  status: string;
  capability_status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  route_ref: string;
  cli_ref: string;
  work_request: {
    request_ref: string;
    safe_summary: string;
    source_surface: string;
  };
  intent: {
    status: string;
    classification_ref: string;
    ambiguity_state: string;
    confidence_label: string;
    low_confidence_asks_user: boolean;
    action_execution_enabled: boolean;
  };
  facts: FounderLoopAgentLoopFact[];
  assumptions: FounderLoopAgentLoopReviewItem[];
  unknowns: FounderLoopAgentLoopReviewItem[];
  plan: {
    status: string;
    revision_ref: string;
    revision_count: number;
    steps: FounderLoopAgentLoopPlanStep[];
  };
  proposed_actions: FounderLoopAgentLoopProposedAction[];
  approval_posture: {
    approval_required_before_mutation: boolean;
    control_center_mints_authority: boolean;
    approval_refs_are_identifiers_only: boolean;
    action_execution_enabled: boolean;
    exact_local_task_lane_visible: boolean;
    decision_route_refs: string[];
  };
  current_state: {
    state: string;
    blocked_state_refs: string[];
    degraded_state_refs: string[];
    next_safe_operator_decision: string;
  };
  evidence: {
    route_ref: string;
    event_count: number;
    evidence_refs: string[];
    proof_refs: string[];
  };
  memory_review: {
    route_ref: string;
    candidate_refs: string[];
    candidate_count: number;
    decision_receipt_refs: string[];
    automatic_memory_write_authorized: boolean;
    context_injection_authorized: boolean;
    next_safe_action: string;
  };
  operator_decision_matrix: FounderLoopOperatorDecisionMatrix;
  surface_bindings: Array<{
    surface: string;
    route_ref: string;
  }>;
  authority_posture: {
    python_core_owns_truth: boolean;
    control_center_mints_authority: boolean;
    runtime_model_calls_enabled: boolean;
    provider_sdk_calls_enabled: boolean;
    live_web_fetching_enabled: boolean;
    browser_automation_enabled: boolean;
    connector_writes_enabled: boolean;
    unrestricted_shell_enabled: boolean;
    plugin_runtime_import_enabled: boolean;
    memory_write_authority_enabled: boolean;
    background_autonomy_enabled: boolean;
    production_authority_enabled: boolean;
  };
  blocked_authority_refs: string[];
  redactions_applied: string[];
}

export interface FounderLoopOperatorDecisionMatrix {
  schema_version: string;
  contract_ref: string;
  status: string;
  capability_status: string;
  source: string;
  backend_owned: boolean;
  control_center_presentation_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  route_ref: string;
  cli_ref: string;
  operator_can_decide_from_cockpit: boolean;
  ui_mints_authority: boolean;
  mutation_controls_enabled: boolean;
  row_count: number;
  rows: FounderLoopOperatorDecisionRow[];
  next_safe_operator_decision: string;
  blocked_authority_refs: string[];
  redactions_applied: string[];
}

export interface FounderLoopOperatorDecisionRow {
  surface: string;
  capability_status: string;
  operator_question: string;
  backend_route_ref: string;
  cli_ref: string;
  primary_ref: string;
  approval_posture: string;
  side_effect_class: string;
  safe_action: string;
  evidence_refs: string[];
  proof_refs: string[];
  receipt_refs: string[];
  blocked_state_refs: string[];
  mutation_enabled: boolean;
  backend_truth_required: boolean;
  no_go_reason: string;
}

export interface FounderLoopTodaySummary {
  schema_version: string;
  status: string;
  surface: string;
  storage_ref: string;
  side_effect_class: string;
  approval_required_before_mutation: boolean;
  product_spine_contract_ref: string;
  required_loop_surfaces: string[];
  required_today_signals: FounderLoopTodaySignal[];
  module_feed_contract: FounderLoopModuleFeedContract[];
  module_completion_contract: FounderLoopModuleCompletionContract;
  evidence_history_contract_ref: string;
  evidence_history_required_states: string[];
  evidence_history_required_questions: FounderLoopEvidenceHistoryQuestion[];
  evidence_history_surface_bindings: FounderLoopEvidenceHistorySurfaceBinding[];
  memory_source_provenance_contract_ref: string;
  memory_source_required_kinds: string[];
  memory_source_policy: FounderLoopMemorySourcePolicy[];
  memory_source_denied_content_refs: string[];
  memory_source_review_posture: FounderLoopMemorySourceReviewPosture;
  memory_review_decision_contract_ref: string;
  memory_review_decision_states: FounderLoopMemoryReviewDecisionState[];
  memory_review_decision_required_ref_fields: string[];
  memory_review_decision_authority_posture: FounderLoopMemoryReviewDecisionAuthorityPosture;
  fcc_memory_review_decision_contract_ref: string;
  fcc_memory_review_decision_route_refs: string[];
  memory_review_decision_receipt_refs: string[];
  memory_review_decision_status: string;
  business_memory_quality_contract_ref: string;
  business_memory_candidate_kinds: FounderLoopBusinessMemoryCandidateKind[];
  business_memory_quality_states: FounderLoopBusinessMemoryQualityState[];
  business_memory_required_ref_fields: string[];
  business_memory_surface_bindings: FounderLoopBusinessMemorySurfaceBinding[];
  business_memory_authority_posture: FounderLoopBusinessMemoryAuthorityPosture;
  business_memory_status: string;
  cross_surface_memory_intake_contract_ref: string;
  cross_surface_memory_intake_status: string;
  cross_surface_memory_intake_required_surfaces: string[];
  cross_surface_memory_intake_required_ref_fields: string[];
  cross_surface_memory_intake_required_blocked_refs: string[];
  cross_surface_memory_intake_proposal_count: number;
  cross_surface_memory_intake_proposals: FounderLoopCrossSurfaceMemoryIntakeProposal[];
  cross_surface_memory_intake_surface_bindings: FounderLoopCrossSurfaceMemoryIntakeSurfaceBinding[];
  cross_surface_memory_intake_authority_posture: FounderLoopCrossSurfaceMemoryIntakeAuthorityPosture;
  cross_surface_memory_intake_blocked_state_refs: string[];
  memory_to_loop_binding_contract_ref: string;
  memory_to_loop_binding_status: string;
  memory_to_loop_required_surfaces: string[];
  memory_to_loop_required_ref_fields: string[];
  memory_derived_action_required_ref_fields: string[];
  memory_to_loop_required_blocked_refs: string[];
  memory_to_loop_item_count: number;
  memory_to_loop_items: FounderLoopMemoryToLoopItem[];
  memory_derived_action_proposal_count: number;
  memory_derived_action_proposals: FounderLoopMemoryDerivedActionProposal[];
  memory_candidate_refs: string[];
  accepted_recall_refs: string[];
  correction_refs: string[];
  rejected_item_refs: string[];
  follow_up_commitment_refs: string[];
  stale_memory_refs: string[];
  missing_evidence_blocker_refs: string[];
  memory_derived_action_proposal_refs: string[];
  memory_to_loop_surface_bindings: FounderLoopMemoryToLoopSurfaceBinding[];
  memory_to_loop_authority_posture: FounderLoopMemoryToLoopAuthorityPosture;
  memory_to_loop_weekly_review_refs: string[];
  weekly_ceo_review_summary: FounderLoopWeeklyCeoReviewSummary;
  memory_to_loop_blocked_state_refs: string[];
  private_beta_readiness_contract_ref: string;
  private_beta_readiness_status: string;
  private_beta_readiness_overall_state: string;
  private_beta_readiness_evidence_packet_ref: string;
  private_beta_readiness_window_ref: string;
  private_beta_readiness_full_strength_goal: string;
  private_beta_readiness_repo_safe_scope: string;
  private_beta_readiness_blocked_authority_summary: string;
  private_beta_readiness_promotion_path_refs: string[];
  private_beta_readiness_product_loop_trial_script_ref: string;
  private_beta_readiness_private_operator_trial_ledger_ref: string;
  private_beta_readiness_required_surfaces: string[];
  private_beta_readiness_acceptance_states: string[];
  private_beta_readiness_acceptance_state_definitions: FounderLoopPrivateBetaReadinessStateDefinition[];
  private_beta_readiness_required_ref_fields: string[];
  private_beta_readiness_required_blocked_refs: string[];
  private_beta_readiness_criterion_count: number;
  private_beta_readiness_criteria: FounderLoopPrivateBetaReadinessCriterion[];
  private_beta_readiness_surface_bindings: FounderLoopPrivateBetaReadinessSurfaceBinding[];
  private_beta_readiness_authority_posture: FounderLoopPrivateBetaReadinessAuthorityPosture;
  private_beta_readiness_blocked_state_refs: string[];
  private_beta_readiness_missing_evidence_refs: string[];
  private_beta_readiness_next_safe_action: string;
  private_beta_readiness_local_private_only: boolean;
  private_beta_readiness_safe_refs_only: boolean;
  private_beta_readiness_review_required: boolean;
  private_beta_readiness_evidence_required: boolean;
  private_beta_readiness_redaction_required: boolean;
  private_beta_readiness_execution_authorized: boolean;
  user_intent_understanding_contract_ref: string;
  user_intent_understanding_status: string;
  user_intent_required_surfaces: string[];
  user_intent_routing_decisions: string[];
  user_intent_required_dependency_refs: string[];
  user_intent_required_ref_fields: string[];
  user_intent_required_blocked_refs: string[];
  user_intent_proposal_count: number;
  user_intent_proposals: FounderLoopUserIntentProposal[];
  user_intent_surface_bindings: FounderLoopUserIntentSurfaceBinding[];
  user_intent_authority_posture: FounderLoopUserIntentAuthorityPosture;
  user_intent_blocked_state_refs: string[];
  user_intent_low_confidence_policy_ref: string;
  user_intent_conflict_policy_ref: string;
  user_intent_next_safe_action: string;
  user_intent_review_required: boolean;
  user_intent_safe_refs_only: boolean;
  user_intent_evidence_required: boolean;
  user_intent_low_confidence_asks_user: boolean;
  user_intent_conflicting_intent_asks_user: boolean;
  user_intent_hidden_authority_enabled: boolean;
  user_intent_action_execution_enabled: boolean;
  chat_local_operator_contract_ref: string;
  chat_local_operator_status: string;
  chat_local_operator_turn_ref: string;
  chat_local_operator_route_ref: string;
  chat_local_operator_model_ref: string;
  chat_local_operator_runtime_truth: string;
  chat_local_operator_auth_truth: string;
  chat_local_operator_tool_denial_truth: string;
  chat_local_operator_tool_denial_ref: string;
  chat_local_operator_safe_evidence_refs: string[];
  chat_local_operator_plans_handoff_ref: string;
  chat_local_operator_actions_handoff_ref: string;
  chat_local_operator_required_truth_fields: string[];
  chat_local_operator_required_blocked_refs: string[];
  chat_local_operator_surface_bindings: FounderLoopChatOperatorSurfaceBinding[];
  chat_local_operator_authority_posture: FounderLoopChatOperatorAuthorityPosture;
  chat_local_operator_blocked_state_refs: string[];
  chat_durable_receipt_contract_ref: string;
  chat_durable_receipt_route_refs: string[];
  chat_durable_receipt_status: string;
  chat_to_loop_handoff_contract_ref?: string;
  chat_to_loop_handoff_read_model?: FounderLoopChatToLoopHandoffReadModel;
  chat_turn_receipt_refs: string[];
  chat_handoff_receipt_refs: string[];
  chat_handoff_created_refs: string[];
  governed_code_workbench_contract_ref: string;
  governed_code_workbench_status: string;
  governed_code_workbench_proposal_ref: string;
  governed_code_workbench_repo_scope_ref: string;
  governed_code_workbench_safe_diff_summary_ref: string;
  governed_code_workbench_validation_plan_ref: string;
  governed_code_workbench_validation_result_refs: string[];
  governed_code_workbench_approval_requirement_ref: string;
  governed_code_workbench_expected_apply_receipt_ref: string;
  governed_code_workbench_expected_rollback_receipt_ref: string;
  governed_code_workbench_evidence_refs: string[];
  governed_code_workbench_idempotency_key_ref: string;
  governed_code_workbench_work_classification?: FounderLoopWorkClassification;
  governed_code_workbench_delegation_proposal?: FounderLoopDelegationProposal;
  governed_code_workbench_cache_context_economics?: FounderLoopCacheContextEconomics;
  governed_code_workbench_safe_summary: string;
  governed_code_workbench_validation_plan_summary: string;
  governed_code_workbench_required_ref_fields: string[];
  governed_code_workbench_required_blocked_refs: string[];
  governed_code_workbench_surface_bindings: FounderLoopGovernedCodeWorkbenchSurfaceBinding[];
  governed_code_workbench_authority_posture: FounderLoopGovernedCodeWorkbenchAuthorityPosture;
  governed_code_workbench_blocked_state_refs: string[];
  operator_workspace_spine_contract_ref?: string;
  operator_workspace_spine_status?: string;
  operator_workspace_spine_read_model?: OperatorWorkspaceSpineReadModel;
  fusion_routing_delegation_contract_ref?: string;
  fusion_routing_delegation_status?: string;
  fusion_routing_delegation_read_model?: FounderLoopFusionRoutingDelegationReadModel;
  fusion_routing_delegation_surface_bindings?: Array<Record<string, string>>;
  fusion_routing_delegation_authority_posture?: Record<string, boolean>;
  fusion_routing_delegation_blocked_state_refs?: string[];
  today_loop_tightening_contract_ref?: string;
  today_loop_read_model?: FounderLoopTodayLoopReadModel;
  follow_up_tracker_contract_ref?: string;
  follow_up_tracker?: FounderLoopFollowUpTrackerReadModel;
  weekly_ceo_review_v1_contract_ref?: string;
  weekly_ceo_review_v1_read_model?: FounderLoopWeeklyCeoReviewV1ReadModel;
  founder_loop_v1_product_proof_contract_ref?: string;
  founder_loop_v1_product_proof_read_model?: FounderLoopProductProofReadModel;
  founder_loop_runs_integration_contract_ref?: string;
  founder_loop_runs_integration_read_model?: FounderLoopRunsIntegrationReadModel;
  loop_trace_refs?: FounderLoopTraceRefs;
  unified_work_thread_contract_ref?: string;
  unified_work_thread_read_model?: FounderLoopUnifiedWorkThreadReadModel;
  evidence_memory_loop_binding_contract_ref?: string;
  evidence_memory_loop_binding_read_model?: FounderLoopEvidenceMemoryLoopBindingReadModel;
  plans_to_actions_bridge_contract_ref?: string;
  plans_to_actions_bridge_read_model?: FounderLoopPlansToActionsBridgeReadModel;
  daily_loop_summary?: FounderLoopDailyLoopSummary;
  source_readiness_items?: FounderLoopSourceReadinessItem[];
  source_readiness_posture?: FounderLoopSourceReadinessPosture;
  crm_lite_relationship_memory_contract_ref?: string;
  crm_lite_relationship_authority_posture?: Record<string, unknown>;
  crm_lite_followups?: FounderLoopCrmLiteFollowUp[];
  memory_why_shown_items?: FounderLoopMemoryWhyShownItem[];
  review_queue_groups?: FounderLoopReviewQueueGroup[];
  weekly_review_narrative?: FounderLoopWeeklyReviewNarrative;
  dogfood_capture?: FounderLoopDogfoodCaptureSummary;
  plans_action_envelope_contract_ref: string;
  plans_action_envelope_review_postures: FounderLoopActionEnvelopeReviewPosture[];
  plans_action_envelope_required_ref_fields: string[];
  plans_action_envelope_required_blocked_refs: string[];
  plans_action_envelope_surface_bindings: FounderLoopActionEnvelopeSurfaceBinding[];
  plans_action_envelope_authority_posture: FounderLoopActionEnvelopeAuthorityPosture;
  plans_action_envelope_status: string;
  task_decomposition_proposal_contract_ref: string;
  task_decomposition_proposal_status: string;
  task_decomposition_proposal_count: number;
  task_decomposition_action_proposal_refs: string[];
  task_decomposition_required_blocked_refs: string[];
  task_decomposition_authority_posture: FounderLoopTaskDecompositionAuthorityPosture;
  priority_refs: string[];
  blocker_refs: string[];
  follow_up_refs: string[];
  plan_action_state: FounderLoopPlanActionState;
  stale_source_posture: FounderLoopStaleSourcePosture;
  next_safe_actions: FounderLoopNextSafeAction[];
  sections: {
    action_inbox_count: number;
    plan_count: number;
    memory_review_count: number;
    briefing_count: number;
    evidence_timeline_count?: number;
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
  evidence_timeline: FounderLoopEvidenceTimelineItem[];
  evidence_timeline_route_ref?: string;
  evidence_timeline_backend_route_ref?: string;
  evidence_timeline_status?: string;
  evidence_timeline_productization_contract_ref?: string;
  evidence_timeline_productized_event_types?: FounderLoopEvidenceEventType[];
  evidence_timeline_productized_group_kinds?: FounderLoopEvidenceGroupKind[];
  evidence_timeline_authority_boundary?: string;
  evidence_timeline_blocked_states?: string[];
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
  action_group_order?: FounderLoopActionGroupId[];
  action_groups?: FounderLoopActionGroupSummary[];
  action_inbox_work_queue_contract_ref?: string;
  action_inbox_work_queue_read_model?: FounderLoopActionInboxWorkQueueReadModel;
  runtime_action_inbox_bridge_contract_ref?: string;
  runtime_action_inbox_bridge_read_model?: FounderLoopRuntimeActionInboxBridgeReadModel;
  action_tool_code_lane_catalog_contract_ref?: string;
  action_tool_code_lane_catalog_read_model?: ActionToolCodeLaneCatalogReadModel;
  action_inbox_decision_lane_contract_ref?: string;
  action_inbox_decision_lane_read_model?: FounderLoopActionInboxDecisionLaneReadModel;
  plans_to_actions_bridge_contract_ref?: string;
  plans_to_actions_bridge_read_model?: FounderLoopPlansToActionsBridgeReadModel;
  chat_to_loop_handoff_contract_ref?: string;
  chat_to_loop_handoff_read_model?: FounderLoopChatToLoopHandoffReadModel;
  items: FounderLoopActionItem[];
  approval_required_before_mutation: boolean;
  mutating_controls_enabled: boolean;
  action_execution_enabled?: boolean;
  decision_route_refs?: string[];
  decision_state_contract_ref?: string;
  decision_statuses?: string[];
  decision_actions?: FounderLoopActionDecisionKind[];
  decision_receipts_required?: boolean;
  idempotency_replay_enabled?: boolean;
  idempotency_conflict_rejected?: boolean;
  today_action_envelope_route_refs?: string[];
  today_action_envelope_receipts_required?: boolean;
  vertical_slice_contract_ref?: string;
  action_envelope_contract_ref?: string;
  action_envelope_review_postures?: FounderLoopActionEnvelopeReviewPosture[];
  action_envelope_required_ref_fields?: string[];
  action_envelope_authority_posture?: FounderLoopActionEnvelopeAuthorityPosture;
  memory_to_loop_binding_contract_ref?: string;
  memory_to_loop_binding_status?: string;
  memory_derived_action_proposals?: FounderLoopMemoryDerivedActionProposal[];
  memory_to_loop_authority_posture?: FounderLoopMemoryToLoopAuthorityPosture;
  memory_to_loop_blocked_state_refs?: string[];
  weekly_ceo_review_summary?: FounderLoopWeeklyCeoReviewSummary;
  private_beta_readiness_contract_ref?: string;
  private_beta_readiness_status?: string;
  private_beta_readiness_overall_state?: string;
  private_beta_readiness_full_strength_goal?: string;
  private_beta_readiness_repo_safe_scope?: string;
  private_beta_readiness_blocked_authority_summary?: string;
  private_beta_readiness_promotion_path_refs?: string[];
  private_beta_readiness_product_loop_trial_script_ref?: string;
  private_beta_readiness_private_operator_trial_ledger_ref?: string;
  private_beta_readiness_criteria?: FounderLoopPrivateBetaReadinessCriterion[];
  private_beta_readiness_authority_posture?: FounderLoopPrivateBetaReadinessAuthorityPosture;
  private_beta_readiness_blocked_state_refs?: string[];
  user_intent_understanding_contract_ref?: string;
  user_intent_understanding_status?: string;
  user_intent_proposals?: FounderLoopUserIntentProposal[];
  user_intent_authority_posture?: FounderLoopUserIntentAuthorityPosture;
  user_intent_blocked_state_refs?: string[];
  source_readiness_items?: FounderLoopSourceReadinessItem[];
  source_readiness_route_ref?: string;
  source_readiness_proposal_candidates?: FounderLoopSourceReadinessProposalCandidate[];
  source_readiness_proposal_binding_contract_ref?: string;
  task_decomposition_action_proposals?: FounderLoopActionItem[];
  task_decomposition_proposal_summary?: FounderLoopTaskDecompositionProposalSummary;
  crm_lite_relationship_memory_contract_ref?: string;
  crm_lite_relationship_authority_posture?: Record<string, unknown>;
  follow_up_tracker_contract_ref?: string;
  follow_up_tracker?: FounderLoopFollowUpTrackerReadModel;
  crm_lite_followups?: FounderLoopCrmLiteFollowUp[];
  memory_why_shown_items?: FounderLoopMemoryWhyShownItem[];
  review_queue_groups?: FounderLoopReviewQueueGroup[];
  dogfood_capture?: FounderLoopDogfoodCaptureSummary;
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
  source_readiness_posture?: FounderLoopSourceReadinessPosture;
  daily_loop_summary?: FounderLoopDailyLoopSummary;
  daily_loop_sections?: FounderLoopBriefingSection[];
  source_readiness_items?: FounderLoopSourceReadinessItem[];
  crm_lite_relationship_memory_contract_ref?: string;
  crm_lite_relationship_authority_posture?: Record<string, unknown>;
  follow_up_tracker_contract_ref?: string;
  follow_up_tracker?: FounderLoopFollowUpTrackerReadModel;
  crm_lite_followups?: FounderLoopCrmLiteFollowUp[];
  memory_why_shown_items?: FounderLoopMemoryWhyShownItem[];
  review_queue_groups?: FounderLoopReviewQueueGroup[];
  weekly_review_narrative?: FounderLoopWeeklyReviewNarrative;
  weekly_ceo_review_v1_contract_ref?: string;
  weekly_ceo_review_v1_read_model?: FounderLoopWeeklyCeoReviewV1ReadModel;
  founder_loop_v1_product_proof_contract_ref?: string;
  founder_loop_v1_product_proof_read_model?: FounderLoopProductProofReadModel;
  founder_loop_runs_integration_contract_ref?: string;
  founder_loop_runs_integration_read_model?: FounderLoopRunsIntegrationReadModel;
  loop_trace_refs?: FounderLoopTraceRefs;
  chat_to_loop_handoff_contract_ref?: string;
  chat_to_loop_handoff_read_model?: FounderLoopChatToLoopHandoffReadModel;
  dogfood_capture?: FounderLoopDogfoodCaptureSummary;
  morning_briefing_v1_contract_ref?: string;
  morning_briefing_v1_read_model?: FounderLoopMorningBriefingV1ReadModel;
  items: FounderLoopBriefingItem[];
  evidence_refs: string[];
  blocked_states: string[];
}

export interface FounderLoopMorningBriefingV1ReadModel {
  schema_version: "product-loop-007-morning-briefing.v1";
  contract_ref: string;
  status: string;
  source: string;
  backend_owned: boolean;
  local_read_model_only: boolean;
  safe_refs_only: boolean;
  raw_content_included: boolean;
  bounded_preview_only: boolean;
  source_readiness_required: boolean;
  missing_sources_visible: boolean;
  item_count: number;
  section_count: number;
  open_action_count: number;
  follow_up_count: number;
  memory_review_count: number;
  source_blocker_count: number;
  safe_summary: string;
  today_summary_ref: string;
  source_readiness_posture_ref: string;
  repo_status_refs: string[];
  workbench_status_refs: string[];
  source_readiness_refs: string[];
  missing_source_refs: string[];
  open_action_refs: string[];
  follow_up_refs: string[];
  memory_review_refs: string[];
  evidence_timeline_refs: string[];
  evidence_refs: string[];
  blocked_state_refs: string[];
  next_safe_action: string;
  authority_boundary: string;
  connector_read_enabled: boolean;
  connector_runtime_enabled: boolean;
  connector_write_enabled: boolean;
  email_calendar_fetch_enabled: boolean;
  account_auth_enabled: boolean;
  live_web_enabled: boolean;
  provider_model_call_enabled: boolean;
  runtime_model_call_enabled: boolean;
  automatic_recommendations_enabled: boolean;
  hidden_memory_write_authorized: boolean;
  memory_write_authorized: boolean;
  context_injection_authorized: boolean;
  action_execution_enabled: boolean;
  repo_write_enabled: boolean;
  workbench_apply_enabled: boolean;
  shell_subprocess_execution_enabled: boolean;
  browser_execution_enabled: boolean;
  notification_delivery_enabled: boolean;
  source_refresh_enabled: boolean;
  production_authority_enabled: boolean;
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
  skill_bundle_proposal_status: string;
  skill_bundle_proposal_count: number;
  skill_bundle_proposal_refs: string[];
  skill_bundle_activation_enabled: boolean;
  skill_bundle_tool_execution_enabled: boolean;
}

export type ProviderCredentialReadinessPosture =
  | "configured"
  | "not_configured"
  | "revoked"
  | "blocked"
  | "validation_blocked"
  | "invocation_blocked"
  | "vault_blocked"
  | "cost_blocked"
  | "unknown_paid_cost_requires_approval";

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
  readiness_posture: ProviderCredentialReadinessPosture;
  credential_configured: boolean;
  credential_revoked: boolean;
  provider_model_refs_bound: boolean;
  cost_governor_binding: ProviderCostGovernorBinding;
  invocation_enabled: boolean;
  credential_material_stored: boolean;
  raw_key_visible: boolean;
  readiness_status: string;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderCostGovernorBinding {
  binding_ref: string;
  provider_ref: string;
  provider_ref_status: "present" | "missing";
  model_ref: string;
  model_ref_status: "present" | "missing";
  credential_ref: string;
  cost_estimate_ref: string;
  budget_decision_ref: string;
  max_approved_usd_ref: string;
  future_receipt_ref: string;
  usage_receipt_ref: string;
  cost_receipt_ref: string;
  cost_governor_posture_ref: string;
  cost_governor_decision_ref: string;
  cost_governor_ref: string;
  readiness_posture:
    | Extract<ProviderCredentialReadinessPosture, "cost_blocked">
    | Extract<
        ProviderCredentialReadinessPosture,
        "unknown_paid_cost_requires_approval"
      >
    | Extract<ProviderCredentialReadinessPosture, "blocked">;
  unknown_paid_cost_requires_approval: boolean;
  estimated_cost_above_budget_blocks_use: boolean;
  provider_model_refs_required: boolean;
  cost_estimate_ref_required: boolean;
  budget_decision_ref_required: boolean;
  max_approved_usd_ref_required: boolean;
  future_receipt_refs_required: boolean;
  provider_usage_claim_requires_receipt_refs: boolean;
  provider_use_authority_granted: boolean;
  credential_validation_authority_granted: boolean;
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  billing_authority_granted: boolean;
  blocker_codes: string[];
  safe_summary: string;
}

export type ProviderSettingsDiagnosticState =
  | "configured"
  | "missing"
  | "blocked"
  | "degraded"
  | "revoked"
  | "expired"
  | "cost_blocked"
  | "disabled"
  | "future_scoped";

export interface ProviderSettingsDiagnosticItem {
  diagnostic_ref: string;
  label: string;
  provider_ref: string;
  model_ref: string;
  credential_ref: string;
  state: ProviderSettingsDiagnosticState;
  state_label: string;
  reason_codes: string[];
  safe_summary: string;
  next_safe_action: string;
  blocked_authority_refs: string[];
  evidence_refs: string[];
  cli_inspection_refs: string[];
  redactions_applied: string[];
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  provider_validation_performed: boolean;
  router_execution_authorized: boolean;
  connector_write_enabled: boolean;
  billing_authority_granted: boolean;
  raw_credential_visible: boolean;
  raw_provider_payload_persisted: boolean;
  settings_mutation_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface ProviderSettingsDiagnosticsSummary {
  schema_version: "provider_settings_diagnostics.v1";
  status: "readable_diagnostics_only";
  safe_summary: string;
  route_refs: string[];
  supported_states: ProviderSettingsDiagnosticState[];
  state_counts: Record<ProviderSettingsDiagnosticState, number>;
  items: ProviderSettingsDiagnosticItem[];
  next_safe_action: string;
  cli_inspection_refs: string[];
  evidence_refs: string[];
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  provider_validation_performed: boolean;
  router_execution_authorized: boolean;
  billing_authority_granted: boolean;
  settings_mutation_enabled: boolean;
  raw_payload_persistence_enabled: boolean;
  production_authority_enabled: boolean;
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
  route_ref: string;
  provider_ref: string;
  provider_manifest_ref: string;
  provider_allowlist_ref: string;
  credential_ref: string;
  consent_ref: string;
  policy_ref: string;
  approval_ref: string;
  revocation_ref: string;
  safe_disable_ref: string;
  idempotency_ref: string;
  validation_enabled: boolean;
  external_validation_allowed: boolean;
  provider_response_persistence_allowed: boolean;
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  billing_authority_granted: boolean;
  exact_approval_required: boolean;
  redacted_receipts_only: boolean;
  validation_receipt_ref: string;
  readiness_status: string;
  ui_states: string[];
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

export interface TinyProviderInvocationReadiness {
  lane_ref: string;
  route_ref: string;
  provider_ref: string;
  model_ref: string;
  provider_scope_refs: string[];
  model_scope_refs: string[];
  policy_scope_refs: string[];
  adapter_scope_refs: string[];
  status:
    | "disabled"
    | "blocked_missing_provider_ref"
    | "blocked_missing_model_ref"
    | "blocked_missing_credential_ref"
    | "blocked_missing_cost_estimate_ref"
    | "blocked_missing_budget_decision_ref"
    | "blocked_missing_max_approved_usd"
    | "blocked_missing_expected_receipt_ref"
    | "blocked_missing_policy_validation"
    | "blocked_provider_not_allowed"
    | "blocked_model_not_allowed"
    | "unknown_paid_cost_blocked"
    | "cost_blocked"
    | "approval_required"
    | "approval_invalid"
    | "approved_no_execution"
    | "live_adapter_blocked"
    | "receipt_recorded";
  invocation_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  network_call_enabled: boolean;
  autonomous_model_call_enabled: boolean;
  background_execution_enabled: boolean;
  billing_authority_granted: boolean;
  exact_approval_required: boolean;
  credential_ref_required: boolean;
  provider_ref_required: boolean;
  model_ref_required: boolean;
  cost_estimate_ref_required: boolean;
  budget_decision_ref_required: boolean;
  max_approved_usd_required: boolean;
  expected_receipt_ref_required: boolean;
  idempotency_ref_required: boolean;
  unknown_paid_cost_blocks: boolean;
  redacted_receipts_only: boolean;
  actual_usage_ref_required: boolean;
  actual_cost_ref_required: boolean;
  receipt_completeness_required: boolean;
  incomplete_cost_requires_review: boolean;
  incomplete_cost_blocks_further_use: boolean;
  receipt_observation_ref: string;
  receipt_state_source: "no_receipt_observed";
  usage_captured: boolean;
  cost_captured: boolean;
  cost_incomplete: boolean;
  review_required: boolean;
  further_use_blocked: boolean;
  prompt_persistence_allowed: boolean;
  response_persistence_allowed: boolean;
  provider_exchange_persistence_allowed: boolean;
  ui_states: TinyProviderInvocationUiState[];
  receipt_observation_supported_states: TinyProviderInvocationReceiptObservationState[];
  blocker_codes: string[];
  safe_summary: string;
}

export type TinyProviderInvocationUiState =
  | "Cost blocked"
  | "Unknown paid cost"
  | "No provider authority"
  | "Disabled no execution"
  | "Live adapter blocked"
  | "Live receipt required";

export type TinyProviderInvocationReceiptObservationState =
  | "Usage captured"
  | "Cost captured"
  | "Cost incomplete"
  | "Review required"
  | "Further use blocked";

export type ProviderRouterDryRunProviderStatus =
  | "eligible"
  | "blocked"
  | "degraded"
  | "cost_risky";

export interface ProviderRouterDryRunProviderProposal {
  provider_ref: string;
  provider_label: string;
  provider_manifest_ref: string;
  model_ref: string;
  credential_ref: string;
  credential_ref_status: string;
  status: ProviderRouterDryRunProviderStatus;
  readiness_status: string;
  eligible_for_exact_approval_scope: boolean;
  missing_credential_ref: string;
  cost_risk_ref: string;
  validation_required_ref: string;
  no_authority_ref: string;
  recommended_approval_scope_ref: string;
  reason_codes: string[];
  proposal_only: boolean;
  execution_authorized: boolean;
  fallback_execution_authorized: boolean;
  network_call_performed: boolean;
  provider_sdk_call_performed: boolean;
  credential_validation_performed: boolean;
  model_invocation_performed: boolean;
  billing_authority_granted: boolean;
  provider_output_authoritative: boolean;
}

export interface ProviderRouterDryRunRecommendedScope {
  approval_scope_ref: string;
  policy_ref: string;
  cost_estimate_ref: string;
  budget_decision_ref: string;
  expected_receipt_ref: string;
  exact_scope_required: boolean;
  provider_ref_required: boolean;
  model_ref_required: boolean;
  credential_ref_required: boolean;
  cost_governor_decision_required: boolean;
  max_approved_usd_required: boolean;
  idempotency_ref_required: boolean;
  receipt_ref_required: boolean;
  execution_authorized_by_scope: boolean;
}

export interface ProviderRouterDryRunReadiness {
  contract_ref: string;
  route_ref: string;
  proposal_ref: string;
  router_run_ref: string;
  idempotency_ref: string;
  status: "proposal_only";
  safe_summary: string;
  safe_refs_only: boolean;
  proposal_only: boolean;
  local_state_only: boolean;
  invocation_authorized: boolean;
  fallback_execution_authorized: boolean;
  network_call_performed: boolean;
  provider_sdk_call_performed: boolean;
  credential_validation_performed: boolean;
  model_invocation_performed: boolean;
  billing_authority_granted: boolean;
  autonomous_background_execution_enabled: boolean;
  prompt_content_persisted: boolean;
  response_content_persisted: boolean;
  provider_payload_content_persisted: boolean;
  provider_proposals: ProviderRouterDryRunProviderProposal[];
  eligible_provider_refs: string[];
  blocked_provider_refs: string[];
  degraded_provider_refs: string[];
  missing_credential_refs: string[];
  cost_risky_refs: string[];
  validation_required_refs: string[];
  no_authority_refs: string[];
  recommended_exact_approval_scope_ref: string;
  recommended_exact_approval_scope: ProviderRouterDryRunRecommendedScope;
  ui_states: string[];
  blocker_codes: string[];
}

export interface ProviderCredentialReadinessSummary {
  status: string;
  safe_summary: string;
  invocation_enabled: boolean;
  raw_key_collection_enabled: boolean;
  credential_material_stored: boolean;
  vault_adapter_configured: boolean;
  supported_readiness_postures: ProviderCredentialReadinessItem["readiness_posture"][];
  posture_counts: Record<
    ProviderCredentialReadinessItem["readiness_posture"],
    number
  >;
  cost_governor_posture_ref: string;
  cost_governor_decision_ref: string;
  cost_governor_binding_required: boolean;
  provider_model_refs_required: boolean;
  cost_estimate_ref_required: boolean;
  budget_decision_ref_required: boolean;
  max_approved_usd_ref_required: boolean;
  future_receipt_refs_required: boolean;
  unknown_paid_cost_requires_approval: boolean;
  estimated_cost_above_budget_blocks_use: boolean;
  provider_usage_claim_requires_receipt_refs: boolean;
  provider_runtime_authority_denied: boolean;
  provider_spend_authority_denied: boolean;
  vault_adapter_readiness: ProviderCredentialVaultAdapterReadiness;
  enrollment_readiness: ProviderCredentialEnrollmentReadiness;
  validation_readiness: ProviderCredentialValidationReadiness;
  invocation_readiness: GovernedProviderInvocationReadiness;
  tiny_invocation_readiness: TinyProviderInvocationReadiness;
  router_dry_run_readiness: ProviderRouterDryRunReadiness;
  provider_settings_diagnostics: ProviderSettingsDiagnosticsSummary;
  providers: ProviderCredentialReadinessItem[];
  blocker_codes: string[];
  future_gate: string;
}

export interface ProviderSourceRef {
  source_ref: string;
  source_kind:
    | "setup"
    | "api_docs"
    | "pricing"
    | "billing"
    | "tokens"
    | "models"
    | "rate_limits"
    | "cost_context";
  label: string;
  url: string;
  last_verified_at: string;
  reviewed_static_metadata: boolean;
  runtime_fetch_performed: boolean;
  provider_call_performed: boolean;
  not_authority: boolean;
}

export interface BudgetPosture {
  budget_posture_ref: string;
  state: "approval_required_for_paid_or_unknown_cost";
  unknown_paid_cost_requires_explicit_approval: boolean;
  estimated_cost_above_budget_blocks_use: boolean;
  provider_model_refs_required: boolean;
  cost_estimate_ref_required: boolean;
  budget_decision_ref_required: boolean;
  receipt_ref_required: boolean;
  max_approved_usd_required: boolean;
  cost_governor_binding_required: boolean;
  provider_use_authority_granted: boolean;
  safe_summary: string;
}

export interface ProviderAuthorityPosture {
  authority_ref: string;
  authority_state: string;
  credential_input_enabled: boolean;
  raw_key_storage_enabled: boolean;
  vault_storage_enabled: boolean;
  credential_validation_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  runtime_network_call_enabled: boolean;
  model_invocation_enabled: boolean;
  automatic_pricing_refresh_enabled: boolean;
  provider_response_persistence_enabled: boolean;
  provider_output_authority_enabled: boolean;
  provider_configuration_enabled: boolean;
  catalog_visibility_grants_authority: boolean;
  billing_authority_claimed: boolean;
  blocker_codes: string[];
  safe_summary: string;
}

export interface ProviderKeyInstruction {
  instruction_ref: string;
  provider_ref: string;
  env_var_styles: string[];
  requires_api_key: boolean;
  setup_source_ref: string;
  api_docs_source_ref: string;
  safe_summary: string;
  credential_input_enabled: boolean;
  raw_key_storage_enabled: boolean;
  vault_storage_enabled: boolean;
  credential_validation_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  credential_material_included: boolean;
}

export interface ProviderCostProfile {
  cost_profile_ref: string;
  provider_ref: string;
  billing_prerequisite: string;
  cost_units: string[];
  token_cost_notes: string[];
  pricing_source_ref: string;
  pricing_may_change: boolean;
  not_billing_authority: boolean;
  reviewed_static_metadata: boolean;
  live_price_amounts_included: boolean;
  automatic_pricing_fetch_enabled: boolean;
  runtime_cost_estimate_enabled: boolean;
  billing_account_authority_enabled: boolean;
  synthetic_examples_only: boolean;
}

export interface ProviderSetupCard {
  provider_ref: string;
  provider_manifest_ref: string;
  provider_label: string;
  provider_class:
    | "direct_model_provider"
    | "router_or_platform"
    | "cloud_or_enterprise_channel"
    | "local_or_open_model_family";
  authority_state: string;
  setup_step_ref: string;
  setup_link: string;
  api_docs_link: string;
  pricing_link: string;
  env_var_styles: string[];
  billing_prerequisite: string;
  token_cost_notes: string[];
  source_refs: ProviderSourceRef[];
  key_instruction: ProviderKeyInstruction;
  cost_profile: ProviderCostProfile;
  authority_posture: ProviderAuthorityPosture;
  last_verified_at: string;
  pricing_may_change: boolean;
  not_billing_authority: boolean;
  guidance_only: boolean;
  credential_input_enabled: boolean;
  raw_key_storage_enabled: boolean;
  credential_validation_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  automatic_pricing_refresh_enabled: boolean;
  provider_output_authority_enabled: boolean;
}

export interface TokenCostExample {
  example_ref: string;
  label: string;
  workload_kind:
    | "quick_chat"
    | "crm_briefing"
    | "long_document_review"
    | "code_task"
    | "batch_analysis";
  safe_summary: string;
  cost_driver_notes: string[];
  synthetic_only: boolean;
  no_live_price_amounts: boolean;
  not_cost_estimate: boolean;
  approval_required_for_paid_use: boolean;
}

export interface ProviderCatalog {
  catalog_ref: string;
  last_verified_at: string;
  provider_cards: ProviderSetupCard[];
  token_cost_examples: TokenCostExample[];
  budget_posture: BudgetPosture;
  blocked_authorities: string[];
  product_language_rules: string[];
  docs_refs: string[];
  verifier_refs: string[];
  redactions_applied: string[];
  no_credential_input: boolean;
  no_raw_key_storage: boolean;
  no_provider_validation: boolean;
  no_provider_sdk_calls: boolean;
  no_model_invocation: boolean;
  no_runtime_web_fetching: boolean;
  no_automatic_pricing_fetch: boolean;
  no_provider_output_authority: boolean;
  catalog_visibility_grants_authority: boolean;
}

export interface ModelProviderAuthoritySummary {
  status: "governed_exact_lanes_only";
  broad_provider_runtime_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  live_provider_network_call_enabled_by_default: boolean;
  exact_tiny_provider_lane_available: boolean;
  exact_tiny_provider_lane_requires_approval: boolean;
  exact_credential_validation_lane_available: boolean;
  exact_credential_validation_requires_approval: boolean;
  provider_router_execution_enabled: boolean;
  provider_router_dry_run_available: boolean;
  model_router_execution_enabled: boolean;
  model_router_trace_available: boolean;
  local_llama_cpp_gateway_available: boolean;
  local_llama_cpp_lifecycle_contract_available: boolean;
  local_llama_cpp_process_started_by_control_plane: boolean;
  shell_execution_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
  raw_prompt_response_provider_payload_persisted: boolean;
  safe_summary: string;
}

export interface ProviderAdapterRuntimePosture {
  adapter_ref: string;
  provider_ref: string;
  model_ref: string;
  model_name_ref: string;
  policy_ref: string;
  endpoint_ref: string;
  transport_ref: string;
  status: "exact_lane_wired_disabled_by_default";
  provider_sdk_call_enabled: boolean;
  network_call_enabled_by_default: boolean;
  network_call_allowed_inside_exact_adapter: boolean;
  credential_ref_required: boolean;
  exact_approval_required: boolean;
  cost_governor_required: boolean;
  receipt_store_required_before_network: boolean;
  redirects_blocked: boolean;
  prompt_persistence_allowed: boolean;
  response_persistence_allowed: boolean;
  provider_payload_persistence_allowed: boolean;
}

export interface ProviderSecretStatusPosture {
  status: "safe_refs_only";
  vault_adapter_status: string;
  validation_readiness_status: string;
  enrollment_status: string;
  credential_ref_statuses: Record<string, string>;
  secret_material_visible: boolean;
  secret_material_persisted_by_repo: boolean;
  transient_secret_resolution_required_for_exact_lanes: boolean;
  raw_key_collection_enabled: boolean;
  safe_summary: string;
}

export interface ProviderNetworkAllowlistPosture {
  status: "exact_endpoint_refs_only";
  allowlist_refs: string[];
  endpoint_refs: string[];
  transport_refs: string[];
  default_network_denied: boolean;
  broad_web_fetch_enabled: boolean;
  provider_sdk_network_enabled: boolean;
  redirects_blocked: boolean;
  post_mutation_scope_enabled: boolean;
  safe_summary: string;
}

export interface ModelMetadataDiscoveryPosture {
  status: "static_metadata_and_local_inventory";
  provider_catalog_ref: string;
  provider_count: number;
  provider_model_refs: string[];
  local_inventory_status: string;
  local_inventory_model_ref_count: number;
  local_gateway_model_ref: string;
  live_provider_model_discovery_enabled: boolean;
  automatic_pricing_fetch_enabled: boolean;
  runtime_provider_metadata_fetch_enabled: boolean;
  safe_summary: string;
}

export interface ProviderCostHookPosture {
  status: "cost_governor_receipt_bound";
  cost_governor_posture_ref: string;
  cost_governor_decision_ref: string;
  cost_estimate_refs_required: boolean;
  budget_decision_refs_required: boolean;
  max_approved_usd_refs_required: boolean;
  expected_receipt_refs_required: boolean;
  actual_usage_cost_refs_required: boolean;
  unknown_paid_cost_blocks: boolean;
  incomplete_actual_cost_blocks_further_use: boolean;
  provider_spend_authority_granted: boolean;
  safe_summary: string;
}

export interface LocalLlamaCppLifecyclePosture {
  status: "local_loopback_lifecycle_governed";
  supervisor_contract_ref: string;
  gateway_contract_ref: string;
  gateway_readiness: Record<string, unknown>;
  model_ref: string;
  loopback_only: boolean;
  structured_argv_only: boolean;
  shell_string_allowed: boolean;
  process_start_performed_by_read_model: boolean;
  model_call_performed_by_read_model: boolean;
  raw_local_path_returned: boolean;
  raw_log_stored: boolean;
  cli_inspection_refs: string[];
  safe_summary: string;
}

export interface ModelRouterTracePosture {
  status: "trace_only_no_execution";
  trace_ref: string;
  decision: Record<string, unknown>;
  provider_router_trace_ref: string;
  provider_router_status: string;
  selected_profile_ref?: string | null;
  selected_model_ref?: string | null;
  candidate_profile_refs: string[];
  rejected_profile_refs: string[];
  reason_codes: string[];
  model_execution_performed: boolean;
  provider_execution_performed: boolean;
  provider_sdk_call_performed: boolean;
  prompt_content_persisted: boolean;
  response_content_persisted: boolean;
  safe_summary: string;
}

export interface ModelProviderResearchProviderPosture {
  provider_id: string;
  provider_label: string;
  provider_kind: string;
  local_remote_posture: "remote_provider_reference" | "local_runtime_reference";
  status:
    | "reference_only"
    | "blocked_missing_refs"
    | "approval_required_exact_lane";
  credential_readiness_status: string;
  cost_latency_metadata_status:
    | "static_cost_metadata_only"
    | "local_inventory_metadata_only";
  supported_authority_mode:
    | "guidance_only"
    | "exact_lane_requires_approval"
    | "local_loopback_metadata_only";
  blocked_reason_ref: string;
  last_safe_diagnostic_receipt_ref: string;
  operator_next_step: string;
  provider_sdk_call_enabled: boolean;
  model_invocation_enabled: boolean;
  credential_material_visible: boolean;
  provider_output_authority_enabled: boolean;
  live_metadata_discovery_enabled: boolean;
}

export interface ModelOutputTruthPosture {
  status: "proposal_and_evidence_not_authority";
  model_output_is_proposal: boolean;
  model_output_is_evidence_candidate: boolean;
  generated_text_is_verified_fact: boolean;
  verified_fact_refs_required: boolean;
  uncertainty_unknowns_required: boolean;
  memory_write_from_model_output_enabled: boolean;
  action_authority_from_model_output_enabled: boolean;
  context_injection_from_model_output_enabled: boolean;
  connector_write_from_model_output_enabled: boolean;
  production_authority_from_model_output_enabled: boolean;
  truth_boundary_ref: string;
  safe_summary: string;
}

export interface ExternalInformationResearchPosture {
  status: "web_access_gateway_deny_by_default";
  web_runtime_authority_contract_ref: string;
  web_access_gateway_required: boolean;
  default_policy_denied: boolean;
  fetched_content_untrusted: boolean;
  fetched_content_instruction_authority_enabled: boolean;
  source_metadata_required: boolean;
  audit_record_required: boolean;
  live_web_fetch_enabled_by_control_plane: boolean;
  browser_observe_enabled_by_control_plane: boolean;
  browser_action_enabled_by_control_plane: boolean;
  provider_search_enabled_by_control_plane: boolean;
  context_injection_from_external_content_enabled: boolean;
  memory_write_from_external_content_enabled: boolean;
  allowed_current_lane_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
}

export interface ModelProviderResearchPosture {
  schema_version: "model_provider_research_posture.v1";
  contract_ref: string;
  source: string;
  status: "metadata_read_model_wired";
  route_ref: "GET /control-center/providers/runtime-control-plane";
  cli_ref: string;
  provider_count: number;
  provider_postures: ModelProviderResearchProviderPosture[];
  model_output_truth: ModelOutputTruthPosture;
  external_information: ExternalInformationResearchPosture;
  proof_refs: string[];
  docs_refs: string[];
  verifier_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  provider_sdk_call_enabled: boolean;
  remote_model_call_enabled: boolean;
  live_web_fetch_enabled: boolean;
  browser_automation_enabled: boolean;
  credential_entry_enabled: boolean;
  memory_write_authorized: boolean;
  action_execution_authorized: boolean;
  context_injection_authorized: boolean;
  production_authority_enabled: boolean;
  broad_autonomy_enabled: boolean;
}

export interface DelegatedRuntimeModelAvailabilityRecord {
  runtime_ref: string;
  runtime_profile_ref: string;
  delegated_runtime_profile_ref: string;
  provider_ref: string;
  model_ref: string;
  display_label: string;
  runtime_availability_status:
    | "runtime_reports_available"
    | "runtime_reports_planned"
    | "local_gateway_metadata_available";
  uaa_invocation_posture:
    | "blocked_no_exact_invocation_lane"
    | "blocked_profile_not_configured"
    | "metadata_only_existing_lane_separate";
  cost_metadata_status:
    | "static_cost_metadata_only"
    | "local_hardware_cost_posture_only"
    | "cost_unknown_blocks_use";
  latency_metadata_status:
    | "static_latency_label_only"
    | "local_gateway_readiness_only"
    | "latency_unknown_blocks_use";
  source_ref: string;
  cost_posture_ref: string;
  latency_posture_ref: string;
  runtime_reported_available: boolean;
  uaa_invocation_allowed: boolean;
  provider_sdk_call_enabled: boolean;
  live_provider_discovery_performed: boolean;
  live_provider_network_call_performed: boolean;
  credential_collection_enabled: boolean;
  credential_material_visible: boolean;
  billing_authority_granted: boolean;
  model_output_authority_enabled: boolean;
  raw_provider_payload_persisted: boolean;
  safe_summary: string;
  blocked_authority_refs: string[];
}

export interface DelegatedRuntimeModelCatalogPosture {
  schema_version: "delegated_runtime_model_catalog.v1";
  contract_ref: string;
  status: "read_only_runtime_model_availability";
  route_ref: "GET /control-center/providers/runtime-control-plane";
  cli_ref: string;
  runtime_profiles_route_ref: string;
  provider_catalog_ref: string;
  model_count: number;
  runtime_profile_count: number;
  runtime_reported_available_count: number;
  uaa_authorized_model_count: number;
  records: DelegatedRuntimeModelAvailabilityRecord[];
  runtime_says_available_is_not_authority: boolean;
  uaa_may_invoke_any_listed_model: boolean;
  static_cost_metadata_only: boolean;
  static_latency_metadata_only: boolean;
  live_provider_discovery_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  remote_model_call_enabled: boolean;
  credential_collection_enabled: boolean;
  billing_authority_granted: boolean;
  model_output_authority_enabled: boolean;
  proof_refs: string[];
  docs_refs: string[];
  verifier_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
}

export interface ModelSlotPostureRecord {
  slot_ref: string;
  slot_role:
    | "main_thinking"
    | "summarization"
    | "title"
    | "approval_scoring"
    | "compression"
    | "retrieval"
    | "vision"
    | "review";
  display_label: string;
  intended_provider_ref: string;
  intended_model_ref: string;
  source_profile_ref: string;
  delegated_runtime_profile_ref: string;
  configured_status:
    | "configured_metadata_only"
    | "planned_not_configured"
    | "runtime_reported_available_not_authorized";
  uaa_execution_posture:
    | "blocked_no_exact_model_authority"
    | "blocked_missing_runtime_profile"
    | "metadata_only_existing_lane_separate";
  provider_readiness_ref: string;
  cost_posture_ref: string;
  latency_posture_ref: string;
  route_decision_trace_ref: string;
  model_output_truth_ref: string;
  warning_refs: string[];
  blocked_authority_refs: string[];
  live_auxiliary_call_enabled: boolean;
  provider_sdk_call_enabled: boolean;
  runtime_selection_mutation_enabled: boolean;
  hidden_model_routing_enabled: boolean;
  route_decision_trace_required: boolean;
  cost_estimate_required: boolean;
  approval_profile_mapping_required: boolean;
  model_output_truth_envelope_required: boolean;
  receipt_required_before_execution: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  safe_summary: string;
}

export interface ModelSlotPostureReadModel {
  schema_version: "hermes_runtime_model_slot_posture.v1";
  contract_ref: string;
  status: "read_only_model_slot_intent";
  route_ref: "GET /control-center/providers/runtime-control-plane";
  cli_ref: string;
  trust_lane_ref: string;
  provider_readiness_ref: string;
  delegated_model_catalog_ref: string;
  slot_count: number;
  warning_count: number;
  records: ModelSlotPostureRecord[];
  main_slot_ref: string;
  auxiliary_slot_refs: string[];
  live_auxiliary_calls_enabled: boolean;
  provider_sdk_use_enabled: boolean;
  runtime_selection_mutation_enabled: boolean;
  hidden_model_routing_enabled: boolean;
  raw_prompt_persistence_enabled: boolean;
  raw_response_persistence_enabled: boolean;
  route_decision_trace_required: boolean;
  cost_estimate_required: boolean;
  approval_profile_mapping_required: boolean;
  model_output_truth_envelope_required: boolean;
  receipts_required_before_execution: boolean;
  proof_refs: string[];
  docs_refs: string[];
  verifier_refs: string[];
  blocked_authority_refs: string[];
  safe_summary: string;
}

export interface ModelProviderControlPlaneReadModel {
  schema_version: "model_provider_control_plane.v1";
  contract_ref: string;
  route_ref: "GET /control-center/providers/runtime-control-plane";
  cli_ref: string;
  status: "governed_control_plane_wired";
  backend_owned: boolean;
  read_only: boolean;
  safe_refs_only: boolean;
  authority: ModelProviderAuthoritySummary;
  provider_adapters: ProviderAdapterRuntimePosture[];
  secret_status: ProviderSecretStatusPosture;
  network_allowlists: ProviderNetworkAllowlistPosture;
  model_metadata_discovery: ModelMetadataDiscoveryPosture;
  cost_hooks: ProviderCostHookPosture;
  local_llama_cpp_lifecycle: LocalLlamaCppLifecyclePosture;
  router_traces: ModelRouterTracePosture[];
  delegated_runtime_model_catalog: DelegatedRuntimeModelCatalogPosture;
  model_slot_posture: ModelSlotPostureReadModel;
  model_provider_research_posture: ModelProviderResearchPosture;
  credential_readiness_ref: string;
  provider_catalog_ref: string;
  exact_lane_route_refs: string[];
  proof_refs: string[];
  blocked_authority_refs: string[];
  docs_refs: string[];
  verifier_refs: string[];
  safe_summary: string;
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
  methods?: string[];
  operation_id: string;
  tags?: string[];
  validation_only: boolean;
  route_group?: string;
  owner?: string;
  service_module?: string;
  side_effect_class?: string;
  route_classification?: string;
  protected_route?: boolean;
  classification_reason?: string;
  risk_class?: string;
  release_status?: string;
  auth_posture?: string;
  blocked_from_production?: boolean;
  evidence_refs?: string[];
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

export interface RuntimeDelegationEndpointPosture {
  endpoint_ref: string;
  endpoint_configured: boolean;
  endpoint_loopback_or_approved_network_required: boolean;
  live_transport_enabled: boolean;
  credential_ref: string;
  credential_material_exposed: boolean;
  network_policy_ref: string;
  safe_summary: string;
}

export interface RuntimeDelegationAdapterReadModel {
  schema_version: "runtime_delegation_adapter.v1";
  contract_ref: string;
  adapter_ref: string;
  runtime_identity_ref: string;
  runtime_label: string;
  runtime_kind: string;
  authority_mode: string;
  status: string;
  endpoint_posture: RuntimeDelegationEndpointPosture;
  capability_refs: string[];
  health_refs: string[];
  proof_refs: string[];
  blocked_reason_refs: string[];
  next_safe_action_refs: string[];
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  uaa_controls_authority: boolean;
  runtime_provides_capability_only: boolean;
  control_center_talks_directly_to_runtime: boolean;
  live_run_submission_enabled: boolean;
  runtime_model_calls_enabled: boolean;
  provider_sdk_calls_enabled: boolean;
  tool_execution_enabled: boolean;
  shell_execution_enabled: boolean;
  browser_automation_enabled: boolean;
  connector_write_enabled: boolean;
  background_autonomy_enabled: boolean;
  production_authority_enabled: boolean;
  safe_refs_only: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  raw_provider_payload_persisted: boolean;
  raw_log_persisted: boolean;
  raw_local_path_persisted: boolean;
  credential_material_persisted: boolean;
  safe_summary: string;
  redactions_applied: string[];
}

export interface RuntimeDiscoveredCapabilityGroup {
  group_ref: string;
  group_kind:
    | "models"
    | "runs"
    | "events"
    | "approvals"
    | "sessions"
    | "skills"
    | "toolsets"
    | "jobs"
    | "blocked_actions";
  runtime_support_status:
    | "reference_only_unverified"
    | "unknown_unreachable"
    | "planned_disabled"
    | "blocked_by_uaa";
  uaa_authorization_status:
    | "read_model_only"
    | "blocked"
    | "approval_required_future_lane";
  runtime_supported_by_reference: boolean;
  uaa_authorized_for_execution: boolean;
  stale_or_unreachable_degrades_to_blocked: boolean;
  trust_label: string;
  safe_summary: string;
  capability_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeToolsetCapabilityRecord {
  toolset_ref: string;
  display_label: string;
  runtime_ref: string;
  profile_ref: string;
  runtime_support_status:
    | "runtime_supported_by_reference"
    | "runtime_configured_metadata_only"
    | "runtime_planned_disabled"
    | "runtime_unsupported"
    | "runtime_blocked_by_uaa";
  uaa_allowance_status:
    | "enabled_read_only"
    | "configured_metadata_only"
    | "approval_required_future_lane"
    | "blocked"
    | "unsupported";
  side_effect_class:
    | "read_only_metadata"
    | "local_workspace"
    | "external_mutation"
    | "high_authority"
    | "unsupported";
  authority_mode_ref: string;
  approval_scope_ref: string;
  safe_disable_ref: string;
  receipt_ref: string;
  verifier_ref: string;
  safe_summary: string;
  runtime_supports_toolset: boolean;
  uaa_allows_execution: boolean;
  tool_invocation_enabled: boolean;
  toolset_config_mutation_enabled: boolean;
  hermes_toolset_enablement_enabled: boolean;
  raw_tool_payload_persisted: boolean;
  blocked_authority_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeToolsetCapabilityPosture {
  schema_version: "runtime_toolset_capability_posture.v1";
  contract_ref: string;
  status: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  authority_profile_ref: string;
  safe_summary: string;
  records: RuntimeToolsetCapabilityRecord[];
  toolset_count: number;
  runtime_supported_count: number;
  uaa_allowed_execution_count: number;
  enabled_read_only_count: number;
  configured_metadata_only_count: number;
  approval_required_future_count: number;
  blocked_count: number;
  unsupported_count: number;
  live_tool_invocation_enabled: boolean;
  toolset_config_mutation_enabled: boolean;
  hermes_toolset_enablement_enabled: boolean;
  raw_tool_payload_persisted: boolean;
  production_authority_enabled: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeToolRegistryEntry {
  tool_ref: string;
  tool_id: string;
  display_label: string;
  origin:
    | "uaa_native"
    | "hermes_reference"
    | "codex_reference"
    | "claude_reference"
    | "mcp_reference"
    | "future_runtime_reference";
  runtime_ref: string;
  toolset_ref: string;
  availability_status:
    | "available_metadata_only"
    | "configured_disabled"
    | "approval_required_future_lane"
    | "blocked"
    | "unsupported";
  configured_status:
    | "configured_metadata_only"
    | "configured_disabled"
    | "unconfigured"
    | "blocked_by_policy"
    | "unsupported";
  authority_class:
    | "validation_only"
    | "preview_only"
    | "approval_required_future_lane"
    | "blocked_high_authority"
    | "unsupported";
  target_kind: string;
  side_effect_class: string;
  risk_class: string;
  approval_requirement: string;
  safe_summary: string;
  uaa_native_catalog_entry: boolean;
  runtime_supported_by_reference: boolean;
  uaa_available_for_preview: boolean;
  uaa_allows_invocation: boolean;
  execution_enabled: boolean;
  remote_discovery_performed: boolean;
  live_web_fetch_performed: boolean;
  provider_model_call_performed: boolean;
  plugin_import_enabled: boolean;
  connector_write_activation_enabled: boolean;
  raw_tool_payload_persisted: boolean;
  approval_scope_ref: string;
  safe_disable_ref: string;
  receipt_plan_ref: string;
  proof_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeToolRegistryAvailabilityReadModel {
  schema_version: "runtime_tool_registry_availability.v1";
  contract_ref: string;
  status: string;
  snapshot_ref: string;
  snapshot_hash_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  capability_discovery_route_ref: string;
  safe_summary: string;
  entries: RuntimeToolRegistryEntry[];
  tool_count: number;
  uaa_native_count: number;
  delegated_reference_count: number;
  available_metadata_only_count: number;
  configured_disabled_count: number;
  approval_required_future_count: number;
  blocked_count: number;
  unsupported_count: number;
  invocation_enabled_count: number;
  preview_available_count: number;
  tool_invocation_enabled: boolean;
  remote_discovery_enabled: boolean;
  live_web_fetch_enabled: boolean;
  provider_model_call_enabled: boolean;
  plugin_import_enabled: boolean;
  connector_write_activation_enabled: boolean;
  raw_tool_payload_persisted: boolean;
  production_authority_enabled: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  next_safe_action_refs: string[];
  redactions_applied: string[];
}

export type RuntimeVirtualAgentRole =
  | "codex_implementer"
  | "claude_reviewer"
  | "hermes_researcher"
  | "local_verifier"
  | "uaa_supervisor"
  | "security_reviewer";

export type RuntimeVirtualProviderPresetStatus =
  | "metadata_only"
  | "readiness_only"
  | "blocked_requires_authority";

export interface RuntimeVirtualAgentSlot {
  slot_ref: string;
  display_label: string;
  role: RuntimeVirtualAgentRole;
  runtime_ref: string;
  provider_ref: string;
  model_ref: string;
  authority_profile_ref: string;
  route_decision_trace_ref: string;
  cost_estimate_ref: string;
  output_envelope_ref: string;
  comparison_proof_ref: string;
  safe_disable_ref: string;
  safe_summary: string;
  proof_refs: string[];
  evidence_refs: string[];
  blocked_authority_refs: string[];
  configured_for_live_call: boolean;
  provider_sdk_call_enabled: boolean;
  external_runtime_dispatch_enabled: boolean;
  hidden_advisor_prompt_enabled: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  output_authoritative: boolean;
  production_authority_enabled: boolean;
}

export interface RuntimeVirtualProviderPreset {
  preset_ref: string;
  display_label: string;
  status: RuntimeVirtualProviderPresetStatus;
  safe_summary: string;
  approval_mode_ref: string;
  route_decision_trace_ref: string;
  cost_estimate_ref: string;
  comparison_proof_ref: string;
  safe_disable_ref: string;
  slots: RuntimeVirtualAgentSlot[];
  slot_count: number;
  proof_refs: string[];
  evidence_refs: string[];
  verifier_refs: string[];
  blocked_authority_refs: string[];
  per_agent_output_envelopes_required: boolean;
  comparison_proof_required: boolean;
  live_model_fanout_enabled: boolean;
  provider_sdk_enabled: boolean;
  external_runtime_dispatch_enabled: boolean;
  hidden_advisor_prompts_enabled: boolean;
  raw_prompt_persistence_enabled: boolean;
  raw_response_persistence_enabled: boolean;
  output_authority_enabled: boolean;
  production_authority_enabled: boolean;
}

export interface RuntimeVirtualProviderMoaReadModel {
  schema_version: "runtime_virtual_provider_moa.v1";
  contract_ref: string;
  status: string;
  snapshot_ref: string;
  snapshot_hash_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  safe_summary: string;
  presets: RuntimeVirtualProviderPreset[];
  preset_count: number;
  agent_slot_count: number;
  ready_preset_count: number;
  blocked_preset_count: number;
  live_model_fanout_enabled: boolean;
  provider_sdk_enabled: boolean;
  external_runtime_dispatch_enabled: boolean;
  hidden_advisor_prompts_enabled: boolean;
  raw_prompt_persistence_enabled: boolean;
  raw_response_persistence_enabled: boolean;
  output_authority_enabled: boolean;
  production_authority_enabled: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  verifier_refs: string[];
  next_safe_action_refs: string[];
  redactions_applied: string[];
}

export interface RuntimeCapabilityDiscoveryReadModel {
  schema_version: "runtime_capability_discovery.v1";
  contract_ref: string;
  snapshot_ref: string;
  snapshot_hash_ref: string;
  runtime_identity_ref: string;
  adapter_ref: string;
  runtime_label: string;
  status: string;
  freshness_status: string;
  runtime_reachable: boolean;
  live_discovery_performed: boolean;
  stale: boolean;
  stale_or_unreachable_degrades_to_blocked: boolean;
  runtime_supported_cannot_grant_uaa_permission: boolean;
  uaa_controls_authority: boolean;
  control_center_talks_directly_to_runtime: boolean;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  freshness_policy_ref: string;
  policy_evaluation_ref: string;
  capability_groups: RuntimeDiscoveredCapabilityGroup[];
  toolset_posture: RuntimeToolsetCapabilityPosture;
  runtime_supported_capability_count: number;
  uaa_authorized_capability_count: number;
  blocked_authority_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
  safe_refs_only: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  raw_provider_payload_persisted: boolean;
  raw_runtime_payload_persisted: boolean;
  raw_log_persisted: boolean;
  raw_local_path_persisted: boolean;
  credential_material_persisted: boolean;
  safe_summary: string;
  redactions_applied: string[];
}

export interface RuntimeRunLifecycleMapping {
  runtime_state:
    | "proposed"
    | "approval_wait"
    | "queued"
    | "running"
    | "stopping"
    | "cancelled"
    | "failed"
    | "completed"
    | "blocked"
    | "unknown_stale";
  uaa_durable_run_state:
    | "proposed"
    | "approval_wait"
    | "queued"
    | "running"
    | "cancellation_requested"
    | "cancelled"
    | "failed"
    | "completed"
    | "blocked"
    | "stale_unknown";
  operator_label: string;
  safe_summary: string;
  receipt_required_before_claim: boolean;
}

export interface RuntimeRunEventRefGrammar {
  grammar_ref: string;
  event_ref_prefix: string;
  required_bindings: string[];
  safe_summary: string;
}

export interface RuntimeRunEventPreview {
  event_ref: string;
  event_kind:
    | "run_proposed"
    | "approval_wait_entered"
    | "event_stream_preview"
    | "stop_requested_preview"
    | "proof_bound";
  runtime_run_ref: string;
  uaa_durable_run_ref: string;
  proof_ref: string;
  redaction_status: string;
  safe_summary: string;
  runtime_payload_persisted: boolean;
  raw_log_persisted: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
}

export interface RuntimeRunProposalReadModel {
  proposal_ref: string;
  runtime_run_ref: string;
  uaa_durable_run_ref: string;
  runtime_state: string;
  uaa_durable_run_state: string;
  create_posture: string;
  stop_posture: string;
  approval_resolution_posture: string;
  event_stream_posture: string;
  create_run_enabled: boolean;
  stop_run_enabled: boolean;
  approval_resolution_enabled: boolean;
  live_event_stream_enabled: boolean;
  retry_recovery_enabled: boolean;
  cancellation_proof_required: boolean;
  event_refs: string[];
  proof_refs: string[];
  receipt_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action_refs: string[];
  safe_summary: string;
}

export interface RuntimeRunEventsReadModel {
  schema_version: "runtime_run_events.v1";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  runtime_identity_ref: string;
  adapter_ref: string;
  status: string;
  lifecycle_mappings: RuntimeRunLifecycleMapping[];
  event_ref_grammar: RuntimeRunEventRefGrammar;
  run_proposals: RuntimeRunProposalReadModel[];
  event_previews: RuntimeRunEventPreview[];
  proposal_count: number;
  approval_wait_count: number;
  completed_run_count: number;
  create_run_route_enabled: boolean;
  stop_run_route_enabled: boolean;
  approval_resolution_route_enabled: boolean;
  live_event_stream_enabled: boolean;
  uaa_controls_authority: boolean;
  control_center_talks_directly_to_runtime: boolean;
  no_mutation_routes_registered: boolean;
  safe_refs_only: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  raw_provider_payload_persisted: boolean;
  raw_runtime_payload_persisted: boolean;
  raw_log_persisted: boolean;
  raw_local_path_persisted: boolean;
  credential_material_persisted: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
  safe_summary: string;
  redactions_applied: string[];
}

export interface RuntimeStreamingProgressEventPreview {
  event_ref: string;
  sequence: number;
  event_kind:
    | "token"
    | "tool_started"
    | "tool_completed"
    | "warning"
    | "approval_wait"
    | "stopped"
    | "failed"
    | "completed";
  runtime_run_ref: string;
  uaa_durable_run_ref: string;
  tool_call_ref?: string | null;
  proof_ref: string;
  event_hash_ref: string;
  redaction_status: string;
  preview_limit_bytes: number;
  safe_summary: string;
  runtime_payload_persisted: boolean;
  raw_tool_payload_persisted: boolean;
  raw_token_persisted: boolean;
  raw_log_persisted: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
}

export interface RuntimeStreamingProgressReadModel {
  schema_version: "runtime_streaming_progress.v1";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  runtime_identity_ref: string;
  runtime_run_ref: string;
  uaa_durable_run_ref: string;
  status: string;
  stream_state:
    | "fixture_preview"
    | "locally_stored_preview"
    | "stale_disconnected"
    | "live_transport_blocked";
  event_previews: RuntimeStreamingProgressEventPreview[];
  event_count: number;
  stale_stream: boolean;
  live_subscription_enabled: boolean;
  sse_transport_enabled: boolean;
  websocket_transport_enabled: boolean;
  reconnect_enabled: boolean;
  event_ingest_enabled: boolean;
  bounded_retention_required: boolean;
  event_hashes_required: boolean;
  uaa_controls_authority: boolean;
  control_center_talks_directly_to_runtime: boolean;
  safe_refs_only: boolean;
  raw_runtime_payload_persisted: boolean;
  raw_tool_payload_persisted: boolean;
  raw_token_persisted: boolean;
  raw_log_persisted: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
  safe_summary: string;
  redactions_applied: string[];
}

export interface RuntimeProfileIsolationRecord {
  profile_ref: string;
  delegated_runtime_profile_ref: string;
  display_label: string;
  role: "coding" | "research" | "operations" | "crm" | "review";
  configured_status:
    | "metadata_configured"
    | "not_configured"
    | "planned_disabled"
    | "blocked";
  authority_profile:
    | "sealed"
    | "read_only_proposal"
    | "approval_required_future_lane";
  authority_profile_ref: string;
  workspace_scope_ref: string;
  memory_scope_ref: string;
  toolset_posture: string;
  profile_health:
    | "healthy_metadata_only"
    | "unconfigured_blocked"
    | "planned_blocked"
    | "needs_operator_review";
  isolated_from_profile_refs: string[];
  configured_for_live_runtime: boolean;
  can_create_runtime_profile: boolean;
  can_delete_runtime_profile: boolean;
  can_write_runtime_config: boolean;
  can_copy_sensitive_material: boolean;
  can_change_runtime_defaults: boolean;
  can_execute_tools: boolean;
  can_call_models: boolean;
  can_write_memory: boolean;
  can_access_workspace_paths: boolean;
  cross_profile_authority_bleed_allowed: boolean;
  safe_summary: string;
  blocked_reason_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeProfileIsolationReadModel {
  schema_version: "runtime_profile_isolation.v1";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  status: string;
  default_uaa_profile_ref: string;
  profiles: RuntimeProfileIsolationRecord[];
  profile_count: number;
  configured_profile_count: number;
  blocked_profile_count: number;
  uaa_profile_refs_separate_from_delegated_runtime_refs: boolean;
  profile_creation_enabled: boolean;
  profile_deletion_enabled: boolean;
  runtime_config_write_enabled: boolean;
  sensitive_material_copy_enabled: boolean;
  runtime_default_change_enabled: boolean;
  cross_profile_authority_bleed_allowed: boolean;
  control_center_mints_profiles: boolean;
  safe_refs_only: boolean;
  raw_profile_names_persisted: boolean;
  raw_workspace_paths_persisted: boolean;
  raw_sensitive_material_persisted: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
  safe_summary: string;
  redactions_applied: string[];
}

export interface RuntimeApprovalScopeValidationResult {
  validation_ref: string;
  requested_scope_ref: string;
  provided_scope_ref: string;
  scope_matches: boolean;
  status: string;
  safe_summary: string;
}

export interface RuntimeApprovalBridgeEnvelope {
  envelope_ref: string;
  runtime_approval_ref: string;
  runtime_run_ref: string;
  uaa_durable_run_ref: string;
  action_inbox_item_ref: string;
  proof_ref: string;
  requested_scope_ref: string;
  idempotency_key_ref: string;
  side_effect_class: string;
  risk_class: string;
  state: string;
  resolution_posture: string;
  timeout_policy_ref: string;
  deny_receipt_ref: string;
  approval_refs_are_identifiers_only: boolean;
  runtime_requested: boolean;
  uaa_approval_recorded: boolean;
  runtime_resolution_sent: boolean;
  approval_resolution_enabled: boolean;
  denial_resolution_enabled: boolean;
  timeout_defaults_to_deny: boolean;
  raw_runtime_payload_persisted: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  safe_summary: string;
  blocked_authority_refs: string[];
  next_safe_action_refs: string[];
}

export interface RuntimeApprovalBridgeDecisionPreview {
  decision_ref: string;
  decision_kind: "approve" | "deny" | "timeout" | "scope_mismatch";
  envelope_ref: string;
  action_inbox_item_ref: string;
  receipt_ref: string;
  runtime_resolution_sent: boolean;
  safe_summary: string;
  blocked_authority_refs: string[];
}

export interface RuntimeApprovalActionInboxProjection {
  action_inbox_item_ref: string;
  source: string;
  lane: string;
  status: string;
  proof_ref: string;
  approval_controls_visible: boolean;
  runtime_resolution_controls_visible: boolean;
  safe_summary: string;
}

export interface RuntimeApprovalBridgeReadModel {
  schema_version: "runtime_approval_bridge.v1";
  contract_ref: string;
  route_ref: string;
  cli_ref: string;
  control_center_ref: string;
  status: string;
  action_inbox_projection: RuntimeApprovalActionInboxProjection;
  envelopes: RuntimeApprovalBridgeEnvelope[];
  decision_previews: RuntimeApprovalBridgeDecisionPreview[];
  scope_validation: RuntimeApprovalScopeValidationResult;
  pending_runtime_approval_count: number;
  denied_preview_count: number;
  timeout_preview_count: number;
  scope_mismatch_count: number;
  runtime_resolution_sent_count: number;
  approval_resolution_route_enabled: boolean;
  deny_resolution_route_enabled: boolean;
  timeout_resolution_route_enabled: boolean;
  uaa_controls_authority: boolean;
  control_center_talks_directly_to_runtime: boolean;
  safe_refs_only: boolean;
  raw_runtime_payload_persisted: boolean;
  raw_prompt_persisted: boolean;
  raw_response_persisted: boolean;
  blocked_authority_refs: string[];
  proof_refs: string[];
  next_safe_action_refs: string[];
  safe_summary: string;
  redactions_applied: string[];
}

export type OperatorRouteInspectionState =
  "checking" | "ready" | "blocked" | "denied" | "degraded" | "unavailable";

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

export interface ControlCenterSettingsStatus {
  schema_version: "uaa-control-center-settings-status.v1";
  module_id: "settings";
  status: "read_only_status";
  route_ref: "GET /control-center/settings/status";
  safe_summary: string;
  maturity_gate_status: string;
  maturity_manifest_ref: string;
  ladder_doc_ref: string;
  verifier_ref: string;
  settings_authority_contract_ref: string;
  settings_authority_verifier_ref: string;
  route_status_manifest_ref: string;
  api_manifest_route_ref: string;
  runtime_readiness_route_ref: string;
  runtime_capability_matrix_ref: string;
  platform_capability_snapshot_ref: string;
  platform_capability_inspection_ref: string;
  review_proposals: string[];
  proposal_review_only: boolean;
  feature_flag_posture: string;
  kill_switch_posture: string;
  disabled_by_default: boolean;
  feature_flag_mutation_enabled: boolean;
  kill_switch_mutation_enabled: boolean;
  settings_mutation_enabled: boolean;
  callable_runtime_authority_enabled: boolean;
  provider_configuration_enabled: boolean;
  installer_behavior_enabled: boolean;
  settings_toggle_grants_authority: boolean;
  catalog_visibility_grants_authority: boolean;
  production_authority_enabled: boolean;
  authority_postures: ControlCenterSettingsAuthorityPosture[];
  kill_switch_postures: ControlCenterSettingsKillSwitchPosture[];
  feature_flag_postures: ControlCenterSettingsFeatureFlagPosture[];
  blocked_authorities: string[];
  missing_contracts: string[];
  redactions_applied: string[];
}

export interface ControlCenterSettingsAuthorityPosture {
  capability_key:
    | "web"
    | "providers"
    | "connectors"
    | "memory_context_use"
    | "model_runtime"
    | "local_model_lifecycle"
    | "platform_capabilities";
  label: string;
  state_label: "Blocked" | "Degraded" | "Partial" | "Metadata only";
  posture_ref: string;
  source_refs: string[];
  safe_summary: string;
  blocked_authority_refs: string[];
  next_safe_action: string;
  callable_runtime_authority: boolean;
  setting_toggle_grants_authority: boolean;
  provider_configuration_enabled: boolean;
  connector_write_enabled: boolean;
  context_injection_enabled: boolean;
  model_call_enabled: boolean;
  local_lifecycle_enabled: boolean;
  installer_behavior_enabled: boolean;
  production_authority_enabled: boolean;
  authority_from_visibility: boolean;
}

export interface ControlCenterSettingsKillSwitchPosture {
  posture_ref: string;
  label: string;
  state_label: "Not configured" | "Blocked" | "Metadata only";
  safe_summary: string;
  revocation_ref: string;
  safe_disable_ref: string;
  evidence_refs: string[];
  next_safe_action: string;
  execution_enabled: boolean;
  revocation_execution_enabled: boolean;
  approval_revocation_enabled: boolean;
  authority_granted: boolean;
  production_authority_enabled: boolean;
}

export interface ControlCenterSettingsFeatureFlagPosture {
  posture_ref: string;
  label: string;
  state_label: "Metadata only" | "Blocked" | "Partial";
  safe_summary: string;
  owner_ref: string;
  evidence_refs: string[];
  next_safe_action: string;
  writable: boolean;
  toggle_enabled: boolean;
  runtime_activation_enabled: boolean;
  authority_granted: boolean;
  production_authority_enabled: boolean;
}

export interface OptionalLocalModelAdapterReadiness {
  adapter_id: "ollama" | "mlx_lm";
  display_name: string;
  readiness_state:
    | "ready"
    | "not_installed"
    | "not_configured"
    | "blocked"
    | "unavailable"
    | "unknown";
  install_detection_posture: string;
  config_detection_posture: string;
  allowed_inspection_refs: string[];
  blocked_authority_refs: string[];
  next_safe_action: string;
  safe_evidence_refs: string[];
  route_refs: string[];
  docs_refs: string[];
  runtime_calls_enabled: boolean;
  model_pulls_enabled: boolean;
  model_downloads_enabled: boolean;
  lifecycle_start_stop_switch_enabled: boolean;
  provider_model_authority_enabled: boolean;
  control_center_subprocess_execution_enabled: boolean;
}

export interface ControlCenterLocalModelsStatus {
  schema_version: "uaa-control-center-local-models-status.v1";
  module_id: "local_models";
  status: "read_only_status";
  route_ref: "GET /control-center/local-models/status";
  safe_summary: string;
  review_proposals: string[];
  proposal_review_only: boolean;
  inventory: Record<string, unknown>;
  gateway_posture: Record<string, unknown>;
  adapter_readiness: OptionalLocalModelAdapterReadiness[];
  lifecycle_actions: Record<string, boolean>;
  blocked_authorities: string[];
  evidence_refs: string[];
  redactions_applied: string[];
}

export interface RedactedLocalChatProbeStatus {
  state: OperatorRouteInspectionState;
  routeRef: string;
  checkedAt: string;
  safeMessage: string;
  contractRef: string;
  turnRef: string;
  modelId: string;
  runtimeTruth: string;
  authTruth: string;
  toolDenialTruth: string;
  toolDenialRef: string;
  evidenceRefs: string[];
  plansHandoffRef: string;
  actionsHandoffRef: string;
  blockedStateRefs: string[];
  modelOutputAuthority: false;
  toolExecutionEnabled: false;
  memoryWriteAuthorized: false;
  contextInjectionAuthorized: false;
  providerSdkCallEnabled: false;
  webFetchEnabled: false;
  connectorWriteEnabled: false;
  shellSubprocessExecutionEnabled: false;
  actionExecutionEnabled: false;
  approvalGrantCaptureEnabled: false;
  productionAuthorityEnabled: false;
  statusCode?: number;
  durationMs?: number;
  responseVisible: false;
  reasonCodes: string[];
  turnHarnessBinding?: TurnHarnessBindingReadModel;
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
  "approved_for_review_only" | "denied_for_review" | "not_captured";

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
  fullStrengthGoal: string;
  repoSafeScope: string;
  blockedAuthoritySummary: string;
  firstRunLoopRefs: string[];
  localPackageProofStatus: string;
  localPackageProofRefs: string[];
  promotionPathRefs: string[];
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
  runtimeDelegationAdapter: RuntimeDelegationAdapterReadModel;
  runtimeCapabilityDiscovery: RuntimeCapabilityDiscoveryReadModel;
  runtimeRunEvents: RuntimeRunEventsReadModel;
  runtimeApprovalBridge: RuntimeApprovalBridgeReadModel;
  runtimeStreamingProgress: RuntimeStreamingProgressReadModel;
  runtimeProfiles: RuntimeProfileIsolationReadModel;
  runtimeToolRegistry: RuntimeToolRegistryAvailabilityReadModel;
  runtimeVirtualProviderMoa: RuntimeVirtualProviderMoaReadModel;
  m15Review: M15ReviewData;
  runAttachedApprovalQueue: RunAttachedApprovalQueue;
  m16Trace: M16TraceData;
  m17Knowledge: M17KnowledgeData;
  m18Runtime: M18RuntimeData;
  m36FileReview: M36FileReviewData;
  m39ContextProposals: M39ContextProposalData;
  macosSetupAssistant: MacOSSetupAssistantData;
  providerCatalog: ProviderCatalog;
  modelProviderControlPlane: ModelProviderControlPlaneReadModel;
  settingsStatus: ControlCenterSettingsStatus;
  localModelsStatus: ControlCenterLocalModelsStatus;
  founderAgentLoopThread: FounderLoopAgentLoopThread;
  founderToday: FounderLoopTodaySummary;
  founderStartHere: ControlCenterStartHereSummary;
  proofIndex: ControlCenterProofIndex;
  trustAuthorityMatrix: TrustAuthorityMatrix;
  codingSession: CodingCockpitSessionReadModel;
  codingContext: CodingWorkspaceContextReadModel;
  codingPatchProposal: CodingPatchProposalReadModel;
  codingPatchApplyReadiness: CodingPatchApplyReadinessReadModel;
  codingTestCommandReadiness: CodingTestCommandReadinessReadModel;
  codingGitReview: CodingGitReviewReadModel;
  codingLivePreview: CodingLivePreviewReadModel;
  codingMultiAgentReview: CodingMultiAgentReviewReadModel;
  workBoard: WorkBoardReadModel;
  founderEvidenceTimeline: FounderLoopEvidenceTimelineIndex;
  founderMemoryReview: FounderLoopMemoryReview;
  founderMemoryWorkbench: FounderLoopMemoryWorkbench;
  founderMemoryContextPacks: FounderLoopMemoryContextPacks;
  founderMemoryRetrievalDiagnostics: FounderLoopMemoryRetrievalDiagnostics;
  founderMemoryCitationIntegrity: FounderLoopMemoryCitationIntegrity;
  founderMemoryQualityIssues: FounderLoopMemoryQualityIssues;
  founderMemoryMaintenanceRuns: FounderLoopMemoryMaintenanceRuns;
  founderMemoryContextManifest: FounderLoopMemoryContextManifest;
  founderActionsInbox: FounderLoopActionsInbox;
  founderMorningBriefing: FounderLoopMorningBriefing;
  founderSourceReadiness: FounderLoopSourceReadiness;
  founderStorageStatus: FounderLoopStorageStatus;
  runObservability: RunObservabilityReadModel;
  crmLocalCommandCenter: CrmLocalCommandCenterReadModel;
  crmM1FixtureShell: CrmM1FixtureShell;
  source: "api" | "mock";
  connection: BackendConnectionSummary;
  routeStates: Record<string, ControlCenterRouteReadState>;
}
