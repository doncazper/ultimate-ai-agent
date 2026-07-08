from __future__ import annotations

from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.code.pair_agent_relay import (
    CodingPairAgentRelayReadModel,
    build_coding_pair_agent_relay_read_model,
)


CODING_COCKPIT_CONTRACT_REF = "contract-ref:coding-cockpit-shell:v1"
CODING_COCKPIT_SESSION_REF = "coding-session:local-readonly-cockpit"
CODING_COCKPIT_CONTEXT_PACK_REF = "context-pack:coding-cockpit-preview-v1"
CODING_COCKPIT_ROUTE_REF = "route-ref:control-center-coding-session"
CODING_COCKPIT_CONTEXT_ROUTE_REF = "route-ref:control-center-coding-context"
CODING_COCKPIT_PATCH_PROPOSAL_REF = "patch-proposal:coding-safe-preview-v1"
CODING_COCKPIT_PATCH_ROUTE_REF = "route-ref:control-center-coding-patch-proposal"
CODING_COCKPIT_PATCH_APPLY_READINESS_REF = (
    "patch-apply-readiness:coding-approved-apply-blocked-v1"
)
CODING_COCKPIT_PATCH_APPLY_ROUTE_REF = (
    "route-ref:control-center-coding-patch-apply-readiness"
)
CODING_COCKPIT_TEST_COMMAND_READINESS_REF = (
    "test-command-readiness:coding-runtime-validation-lanes-v1"
)
CODING_COCKPIT_TEST_COMMAND_ROUTE_REF = (
    "route-ref:control-center-coding-test-command-readiness"
)
CODING_COCKPIT_GIT_REVIEW_REF = "git-review:coding-readonly-review-blocked-v1"
CODING_COCKPIT_GIT_REVIEW_ROUTE_REF = "route-ref:control-center-coding-git-review"
CODING_COCKPIT_LIVE_PREVIEW_REF = "live-preview:coding-status-blocked-v1"
CODING_COCKPIT_LIVE_PREVIEW_ROUTE_REF = (
    "route-ref:control-center-coding-live-preview"
)
CODING_COCKPIT_MULTI_AGENT_REVIEW_REF = "multi-agent-review:coding-blocked-v1"
CODING_COCKPIT_MULTI_AGENT_REVIEW_ROUTE_REF = (
    "route-ref:control-center-coding-multi-agent-review"
)
CODING_COCKPIT_PROJECT_MODEL_REF = "coding-project-model:local-uaa-posture-v1"
CODING_COCKPIT_BACKEND_ROUTE_REF = "GET /control-center/coding/session"
CODING_COCKPIT_CONTEXT_BACKEND_ROUTE_REF = "GET /control-center/coding/context"
CODING_COCKPIT_PATCH_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/patch-proposal"
)
CODING_COCKPIT_PATCH_APPLY_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/patch-apply-readiness"
)
CODING_COCKPIT_TEST_COMMAND_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/test-command-readiness"
)
CODING_COCKPIT_GIT_REVIEW_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/git-review"
)
CODING_COCKPIT_LIVE_PREVIEW_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/live-preview"
)
CODING_COCKPIT_MULTI_AGENT_REVIEW_BACKEND_ROUTE_REF = (
    "GET /control-center/coding/multi-agent-review"
)
CODING_COCKPIT_FRONTEND_ROUTE_REF = "/coding"
CODING_COCKPIT_REQUIRED_BLOCKED_REFS = [
    "blocked-state:coding-no-file-write",
    "blocked-state:coding-no-shell-subprocess",
    "blocked-state:coding-no-git-mutation",
    "blocked-state:coding-no-provider-model-call",
    "blocked-state:coding-no-browser-automation",
    "blocked-state:coding-no-connector-write",
    "blocked-state:coding-no-background-autonomy",
    "blocked-state:coding-no-production-authority",
]


AuthorityModeState = Literal["current", "planned", "blocked", "hard_gate"]
CockpitPanelState = Literal[
    "backend_owned",
    "read_only",
    "proposal_only",
    "preview_only",
    "blocked",
    "planned",
]
CockpitTaskStatus = Literal["read_only_seed", "proposal_only_blocked_runtime"]
ContextRefKind = Literal["file", "folder", "exclude_rule", "search_ref"]
ContextRefStatus = Literal["included", "excluded", "candidate", "blocked"]
ContextBudgetState = Literal["within_budget", "near_limit", "over_limit_blocked"]
PatchChangeKind = Literal["modify", "add", "delete_blocked", "generated_blocked"]
PatchProposalStatus = Literal["proposal_artifact_preview"]
PatchApplyReadinessStatus = Literal["blocked_missing_exact_apply_contract"]
PatchApplyPrerequisiteStatus = Literal["present", "missing", "blocked"]
TestCommandReadinessStatus = Literal[
    "approval_required_runtime_lane_available",
    "blocked_missing_allowlisted_command_authority",
]
TestCommandKind = Literal[
    "focused_pytest",
    "repo_verifier",
    "frontend_check",
    "repo_doctor",
]
GitReviewStatus = Literal["blocked_missing_git_review_authority"]
GitReviewItemKind = Literal[
    "status",
    "diff",
    "changed_files",
    "commit_proposal",
    "pr_description_proposal",
]
LivePreviewStatus = Literal["blocked_missing_live_preview_authority"]
LivePreviewItemKind = Literal[
    "dev_server_status",
    "preview_url",
    "screenshot",
    "console_errors",
    "visual_regression",
    "route_checklist",
    "viewport",
]
MultiAgentReviewStatus = Literal["blocked_missing_multi_agent_authority"]
AgentReviewSlotKind = Literal[
    "implementer",
    "reviewer",
    "local_verifier",
    "security_reviewer",
    "ux_reviewer",
    "test_fixer",
    "merge_captain",
]
CodingProjectCapabilityKind = Literal[
    "workspace",
    "repo",
    "lane",
    "branch",
    "worktree",
    "files",
    "diffs",
    "tests",
    "preview",
    "terminal",
    "git",
    "proof",
]
CodingProjectCapabilityState = Literal[
    "read_only",
    "proposal_only",
    "blocked",
    "planned",
]


class CodingCockpitAuthorityMode(BaseModel):
    mode_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=80)
    state: AuthorityModeState
    operator_posture: str = Field(..., min_length=1, max_length=160)
    safe_summary: str = Field(..., min_length=1, max_length=360)
    allowed_now: bool
    planned: bool
    blocked: bool
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_mode(self) -> "CodingCockpitAuthorityMode":
        validate_task_ref(self.mode_ref, "mode_ref")
        for ref in self.blocked_authority_refs + self.promotion_path_refs:
            validate_task_ref(ref, "authority_mode_ref")
        for value in [
            self.label,
            self.state,
            self.operator_posture,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "authority_mode_text")
        if self.state in {"blocked", "hard_gate"} and not self.blocked:
            raise ValueError("blocked authority mode must be blocked")
        if self.state == "current" and not self.allowed_now:
            raise ValueError("current authority mode must be allowed now")
        return self


class CodingCockpitRefItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "CodingCockpitRefItem":
        validate_task_ref(self.item_ref, "item_ref")
        for ref in (
            self.source_refs
            + self.evidence_refs
            + self.proof_refs
            + self.blocked_authority_refs
        ):
            validate_task_ref(ref, "coding_item_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_item_text")
        return self


class CodingCockpitPreviewPanel(BaseModel):
    panel_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    state: CockpitPanelState
    safe_summary: str = Field(..., min_length=1, max_length=520)
    items: list[CodingCockpitRefItem] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=360)
    mutation_enabled: bool = False
    runtime_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_panel(self) -> "CodingCockpitPreviewPanel":
        validate_task_ref(self.panel_ref, "panel_ref")
        for ref in self.proof_refs + self.blocked_authority_refs:
            validate_task_ref(ref, "coding_panel_ref")
        for value in [self.title, self.state, self.safe_summary, self.next_safe_action]:
            validate_safe_task_text(value, "coding_panel_text")
        if self.mutation_enabled:
            raise ValueError("coding cockpit panel cannot enable mutation")
        if self.runtime_authority_enabled:
            raise ValueError("coding cockpit panel cannot enable runtime authority")
        return self


class CodingProjectCapabilityReadModel(BaseModel):
    capability_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    capability_kind: CodingProjectCapabilityKind
    state: CodingProjectCapabilityState
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    browser_automation_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_autonomy_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_capability(self) -> "CodingProjectCapabilityReadModel":
        for ref in [
            self.capability_ref,
            *self.source_refs,
            *self.evidence_refs,
            *self.proof_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
        ]:
            validate_task_ref(ref, "coding_project_capability_ref")
        for value in [
            self.label,
            self.capability_kind,
            self.state,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "coding_project_capability_text")
        required_false_flags = {
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding project capability enabled {enabled[0]}")
        if self.state == "blocked" and not self.blocked_authority_refs:
            raise ValueError("blocked project capability needs blocker refs")
        return self


class CodingProjectModelReadModel(BaseModel):
    schema_version: Literal["uaa-coding-project-model.v1"] = (
        "uaa-coding-project-model.v1"
    )
    project_model_ref: str = CODING_COCKPIT_PROJECT_MODEL_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    workspace_ref: str = "workspace-ref:coding:local-uaa"
    repo_scope_ref: str = "repo-scope:coding:local-uaa"
    branch_ref: str = "branch-ref:coding:current-local"
    worktree_ref: str = "worktree-ref:coding:current-local-readonly"
    lane_ref: str = "coding-lane:project-model-readonly"
    route_ref: str = CODING_COCKPIT_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-project-model"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:hermes-runtime-coding-project-model",
            "docs-ref:control-center-coding-cockpit",
        ]
    )
    status: Literal["read_only_project_posture"] = "read_only_project_posture"
    project_label: str = Field(..., min_length=1, max_length=120)
    repo_label: str = Field(..., min_length=1, max_length=120)
    branch_label: str = Field(..., min_length=1, max_length=120)
    worktree_label: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    capabilities: list[CodingProjectCapabilityReadModel] = Field(
        default_factory=list
    )
    capability_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_content_included: bool = False
    repo_file_read_performed: bool = False
    project_scan_performed: bool = False
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_status_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    dev_server_control_enabled: bool = False
    browser_preview_enabled: bool = False
    browser_automation_enabled: bool = False
    provider_model_call_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_project_model(self) -> "CodingProjectModelReadModel":
        for ref in [
            self.project_model_ref,
            self.session_ref,
            self.workspace_ref,
            self.repo_scope_ref,
            self.branch_ref,
            self.worktree_ref,
            self.lane_ref,
            self.route_ref,
            *self.capability_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
        ]:
            validate_task_ref(ref, "coding_project_model_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.project_label,
                self.repo_label,
                self.branch_label,
                self.worktree_label,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_project_model_text")
        if not self.capabilities:
            raise ValueError("coding project model needs capability refs")
        capability_refs = {item.capability_ref for item in self.capabilities}
        if len(capability_refs) != len(self.capabilities):
            raise ValueError("coding project model capability refs must be unique")
        if set(self.capability_refs) != capability_refs:
            raise ValueError("capability refs must match capabilities")
        kinds = {item.capability_kind for item in self.capabilities}
        required_kinds = set(get_args(CodingProjectCapabilityKind))
        missing_kinds = required_kinds - kinds
        if missing_kinds:
            raise ValueError("coding project model missing capability kinds")
        required_false_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "repo_file_read_performed": self.repo_file_read_performed,
            "project_scan_performed": self.project_scan_performed,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_status_execution_enabled": self.git_status_execution_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "dev_server_control_enabled": self.dev_server_control_enabled,
            "browser_preview_enabled": self.browser_preview_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding project model enabled {enabled[0]}")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding project model disabled {disabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_project_model")
        return self


class CodingContextRefReadModel(BaseModel):
    context_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    ref_kind: ContextRefKind
    status: ContextRefStatus
    include_reason: str = Field(..., min_length=1, max_length=360)
    token_estimate: int = Field(..., ge=0, le=25000)
    operator_selected: bool = False
    agent_selected: bool = False
    included_in_preview: bool = False
    excluded_from_preview: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=420)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_path_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_context_ref(self) -> "CodingContextRefReadModel":
        validate_task_ref(self.context_ref, "context_ref")
        for ref in (
            self.source_refs
            + self.evidence_refs
            + self.proof_refs
            + self.blocked_authority_refs
        ):
            validate_task_ref(ref, "context_ref_link")
        for value in [
            self.label,
            self.ref_kind,
            self.status,
            self.include_reason,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "coding_context_ref_text")
        if self.raw_path_included:
            raise ValueError("coding context ref cannot include raw paths")
        if self.raw_content_included:
            raise ValueError("coding context ref cannot include raw content")
        if self.status == "included" and not self.included_in_preview:
            raise ValueError("included context ref must be in preview")
        if self.status == "excluded" and not self.excluded_from_preview:
            raise ValueError("excluded context ref must be excluded from preview")
        return self


class CodingContextComparisonReadModel(BaseModel):
    comparison_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    operator_context_ref: str = Field(..., min_length=1)
    agent_context_ref: str = Field(..., min_length=1)
    status: Literal["aligned", "operator_only", "agent_only", "blocked"]
    safe_summary: str = Field(..., min_length=1, max_length=420)
    proof_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_comparison(self) -> "CodingContextComparisonReadModel":
        for ref in [
            self.comparison_ref,
            self.operator_context_ref,
            self.agent_context_ref,
            *self.proof_refs,
        ]:
            validate_task_ref(ref, "context_comparison_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "context_comparison_text")
        return self


class CodingWorkspaceContextReadModel(BaseModel):
    schema_version: Literal["uaa-coding-workspace-context.v1"] = (
        "uaa-coding-workspace-context.v1"
    )
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    route_ref: str = CODING_COCKPIT_CONTEXT_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_CONTEXT_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-context"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    status: Literal["read_only_context_pack_preview"] = (
        "read_only_context_pack_preview"
    )
    budget_state: ContextBudgetState = "within_budget"
    token_budget_limit: int = Field(default=24000, ge=1, le=250000)
    token_estimate_total: int = Field(default=0, ge=0, le=250000)
    token_budget_remaining: int = Field(default=0, ge=0, le=250000)
    context_refs: list[CodingContextRefReadModel] = Field(default_factory=list)
    operator_selected_refs: list[str] = Field(default_factory=list)
    agent_selected_refs: list[str] = Field(default_factory=list)
    excluded_refs: list[str] = Field(default_factory=list)
    search_refs: list[str] = Field(default_factory=list)
    comparison: list[CodingContextComparisonReadModel] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    preview_only: bool = True
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_content_included: bool = False
    repo_file_read_performed: bool = False
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_context(self) -> "CodingWorkspaceContextReadModel":
        for ref in [
            self.context_pack_ref,
            self.session_ref,
            self.route_ref,
            *self.operator_selected_refs,
            *self.agent_selected_refs,
            *self.excluded_refs,
            *self.search_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.redactions_applied,
            *self.docs_refs,
        ]:
            validate_task_ref(ref, "coding_context_pack_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [self.status, self.budget_state, self.next_safe_action]
        ):
            validate_safe_task_text(value, "coding_context_pack_text")
        if self.token_estimate_total != sum(
            item.token_estimate for item in self.context_refs if item.included_in_preview
        ):
            raise ValueError("context token estimate must match included refs")
        if self.token_budget_remaining != max(
            self.token_budget_limit - self.token_estimate_total, 0
        ):
            raise ValueError("context token budget remaining is inconsistent")
        included_refs = {
            item.context_ref for item in self.context_refs if item.included_in_preview
        }
        if not set(self.operator_selected_refs).issubset(included_refs):
            raise ValueError("operator selected refs must be included")
        if not set(self.agent_selected_refs).issubset(included_refs):
            raise ValueError("agent selected refs must be included")
        context_ref_set = {item.context_ref for item in self.context_refs}
        if not set(self.search_refs).issubset(context_ref_set):
            raise ValueError("search refs must exist in context refs")
        excluded_context_ref_set = {
            item.context_ref for item in self.context_refs if item.excluded_from_preview
        }
        if not set(self.excluded_refs).issubset(
            excluded_context_ref_set
        ):
            raise ValueError("excluded refs must be excluded")
        required_false_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "repo_file_read_performed": self.repo_file_read_performed,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding context enabled {enabled[0]}")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "preview_only": self.preview_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding context disabled {disabled[0]}")
        return self


class CodingPatchProposalFileReadModel(BaseModel):
    change_ref: str = Field(..., min_length=1)
    file_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    change_kind: PatchChangeKind
    status: Literal["proposed", "blocked"]
    hunk_refs: list[str] = Field(default_factory=list)
    additions: int = Field(default=0, ge=0, le=5000)
    deletions: int = Field(default=0, ge=0, le=5000)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_path_included: bool = False
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_patch_file(self) -> "CodingPatchProposalFileReadModel":
        for ref in [
            self.change_ref,
            self.file_ref,
            *self.hunk_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_patch_file_ref")
        for value in [
            self.label,
            self.change_kind,
            self.status,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "coding_patch_file_text")
        if self.raw_path_included:
            raise ValueError("coding patch file cannot include raw paths")
        if self.raw_content_included:
            raise ValueError("coding patch file cannot include raw content")
        if self.status == "blocked" and not self.blocked_authority_refs:
            raise ValueError("blocked patch file requires blocked authority refs")
        return self


class CodingPatchProposalReadModel(BaseModel):
    schema_version: Literal["uaa-coding-patch-proposal.v1"] = (
        "uaa-coding-patch-proposal.v1"
    )
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    route_ref: str = CODING_COCKPIT_PATCH_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_PATCH_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-patch-proposal"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    status: PatchProposalStatus = "proposal_artifact_preview"
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    proposed_file_refs: list[str] = Field(default_factory=list)
    file_changes: list[CodingPatchProposalFileReadModel] = Field(default_factory=list)
    diff_preview_refs: list[str] = Field(default_factory=list)
    diff_summary_lines: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    proposal_only: bool = True
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_content_included: bool = False
    repo_file_read_performed: bool = False
    patch_apply_enabled: bool = False
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_patch_proposal(self) -> "CodingPatchProposalReadModel":
        for ref in [
            self.patch_proposal_ref,
            self.session_ref,
            self.context_pack_ref,
            self.route_ref,
            *self.proposed_file_refs,
            *self.diff_preview_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.redactions_applied,
            *self.docs_refs,
        ]:
            validate_task_ref(ref, "coding_patch_proposal_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [self.status, self.title, self.safe_summary, self.next_safe_action]
            + self.diff_summary_lines
        ):
            validate_safe_task_text(value, "coding_patch_proposal_text")
        file_ref_set = {change.file_ref for change in self.file_changes}
        if set(self.proposed_file_refs) != file_ref_set:
            raise ValueError("proposed file refs must match patch file changes")
        hunk_ref_set = {
            hunk_ref for change in self.file_changes for hunk_ref in change.hunk_refs
        }
        if not set(self.diff_preview_refs).issubset(hunk_ref_set):
            raise ValueError("diff preview refs must be patch hunk refs")
        required_false_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "repo_file_read_performed": self.repo_file_read_performed,
            "patch_apply_enabled": self.patch_apply_enabled,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding patch proposal enabled {enabled[0]}")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "proposal_only": self.proposal_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding patch proposal disabled {disabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_patch_proposal")
        return self


class CodingPatchApplyPrerequisiteReadModel(BaseModel):
    prerequisite_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    status: PatchApplyPrerequisiteStatus
    safe_summary: str = Field(..., min_length=1, max_length=420)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_prerequisite(self) -> "CodingPatchApplyPrerequisiteReadModel":
        for ref in [
            self.prerequisite_ref,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_patch_apply_prerequisite_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_patch_apply_prerequisite_text")
        if self.status in {"missing", "blocked"} and not self.blocked_authority_refs:
            raise ValueError("missing or blocked apply prerequisite needs blocker refs")
        return self


class CodingPatchApplyReadinessReadModel(BaseModel):
    schema_version: Literal["uaa-coding-patch-apply-readiness.v1"] = (
        "uaa-coding-patch-apply-readiness.v1"
    )
    readiness_ref: str = CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    route_ref: str = CODING_COCKPIT_PATCH_APPLY_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_PATCH_APPLY_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_coding.py inspect-patch-apply-readiness"
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:coding-approved-patch-apply-blocker",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    unblock_prompt_refs: list[str] = Field(
        default_factory=lambda: ["prompt-ref:unblock-coding-approved-patch-apply"]
    )
    status: PatchApplyReadinessStatus = "blocked_missing_exact_apply_contract"
    title: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    required_authority_profile_refs: list[str] = Field(default_factory=list)
    prerequisites: list[CodingPatchApplyPrerequisiteReadModel] = Field(
        default_factory=list
    )
    expected_receipt_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    readiness_only: bool = True
    safe_refs_only: bool = True
    raw_paths_included: bool = False
    raw_content_included: bool = False
    repo_file_read_performed: bool = False
    exact_patch_body_available: bool = False
    hunk_selection_contract_available: bool = False
    checkpoint_contract_available: bool = False
    approval_binding_available: bool = False
    rollback_contract_available: bool = False
    patch_apply_enabled: bool = False
    file_write_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    rollback_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_patch_apply_readiness(self) -> "CodingPatchApplyReadinessReadModel":
        for ref in [
            self.readiness_ref,
            self.session_ref,
            self.context_pack_ref,
            self.patch_proposal_ref,
            self.route_ref,
            *self.required_authority_profile_refs,
            *self.expected_receipt_refs,
            *self.rollback_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_patch_apply_readiness_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.title,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_patch_apply_readiness_text")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "readiness_only": self.readiness_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding patch apply readiness disabled {disabled[0]}")
        required_false_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "repo_file_read_performed": self.repo_file_read_performed,
            "exact_patch_body_available": self.exact_patch_body_available,
            "hunk_selection_contract_available": self.hunk_selection_contract_available,
            "checkpoint_contract_available": self.checkpoint_contract_available,
            "approval_binding_available": self.approval_binding_available,
            "rollback_contract_available": self.rollback_contract_available,
            "patch_apply_enabled": self.patch_apply_enabled,
            "file_write_enabled": self.file_write_enabled,
            "approval_grant_capture_enabled": self.approval_grant_capture_enabled,
            "rollback_execution_enabled": self.rollback_execution_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding patch apply readiness enabled {enabled[0]}")
        if not any(item.status in {"missing", "blocked"} for item in self.prerequisites):
            raise ValueError("patch apply readiness needs at least one blocker")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_patch_apply_readiness")
        return self


class CodingSuggestedTestCommandReadModel(BaseModel):
    command_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    command_kind: TestCommandKind
    status: Literal["approval_required_runtime_lane", "suggested_blocked"]
    safe_command_summary: str = Field(..., min_length=1, max_length=420)
    allowlist_ref: str = Field(..., min_length=1)
    runtime_lane_ref: str = Field(..., min_length=1)
    runtime_command_intent: str = Field(..., min_length=1, max_length=80)
    execution_route_ref: str = "POST /api/runtime/invocations/{id}/execute"
    execution_cli_ref: str = "scripts/dev/uaa_runtime.py receipts"
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    expected_receipt_ref: str = Field(..., min_length=1)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    approval_required: bool = True
    exact_runtime_lane_available: bool = True
    raw_command_included: bool = False
    raw_output_included: bool = False
    command_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_suggested_command(self) -> "CodingSuggestedTestCommandReadModel":
        for ref in [
            self.command_ref,
            self.allowlist_ref,
            self.runtime_lane_ref,
            self.expected_receipt_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_suggested_test_command_ref")
        for value in [
            self.label,
            self.command_kind,
            self.status,
            self.safe_command_summary,
            self.runtime_command_intent,
            self.execution_route_ref,
            self.execution_cli_ref,
            self.approval_scope_ref,
        ]:
            validate_safe_task_text(value, "coding_suggested_test_command_text")
        if not self.blocked_authority_refs:
            raise ValueError("suggested test command needs blocker refs")
        if self.status == "approval_required_runtime_lane":
            if not self.approval_required or not self.exact_runtime_lane_available:
                raise ValueError("coding suggested command runtime lane required")
        required_false_flags = {
            "raw_command_included": self.raw_command_included,
            "raw_output_included": self.raw_output_included,
            "command_execution_enabled": self.command_execution_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding suggested command enabled {enabled[0]}")
        return self


class CodingTestCommandReadinessReadModel(BaseModel):
    schema_version: Literal["uaa-coding-test-command-readiness.v1"] = (
        "uaa-coding-test-command-readiness.v1"
    )
    readiness_ref: str = CODING_COCKPIT_TEST_COMMAND_READINESS_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    patch_apply_readiness_ref: str = CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    route_ref: str = CODING_COCKPIT_TEST_COMMAND_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_TEST_COMMAND_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_coding.py inspect-test-command-readiness"
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:coding-validation-runtime-lane",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    unblock_prompt_refs: list[str] = Field(default_factory=list)
    status: TestCommandReadinessStatus = (
        "approval_required_runtime_lane_available"
    )
    title: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    allowlist_refs: list[str] = Field(default_factory=list)
    suggested_commands: list[CodingSuggestedTestCommandReadModel] = Field(
        default_factory=list
    )
    expected_receipt_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    runtime_gateway_execution_route_refs: list[str] = Field(
        default_factory=lambda: ["POST /api/runtime/invocations/{id}/execute"]
    )
    runtime_gateway_cli_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_runtime.py inspect-action-inbox-bridge",
            "scripts/dev/uaa_runtime.py receipts",
        ]
    )
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    authority_domain_ref: str = "authority-domain:workspace"
    authority_capability_ref: str = "authority-capability:execute"
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    readiness_only: bool = True
    safe_refs_only: bool = True
    approval_required: bool = True
    exact_runtime_lane_available: bool = True
    runtime_gateway_receipts_available: bool = True
    raw_command_included: bool = False
    raw_output_included: bool = False
    command_output_summary_included: bool = False
    exit_code_available: bool = False
    test_receipt_created: bool = False
    command_execution_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    arbitrary_shell_enabled: bool = False
    install_command_enabled: bool = False
    network_command_enabled: bool = False
    destructive_command_enabled: bool = False
    background_process_enabled: bool = False
    file_write_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_test_command_readiness(self) -> "CodingTestCommandReadinessReadModel":
        for ref in [
            self.readiness_ref,
            self.session_ref,
            self.context_pack_ref,
            self.patch_proposal_ref,
            self.patch_apply_readiness_ref,
            self.route_ref,
            *self.allowlist_refs,
            *self.expected_receipt_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            self.authority_domain_ref,
            self.authority_capability_ref,
            *self.redactions_applied,
            *self.docs_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_test_command_readiness_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.title,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.approval_scope_ref,
                self.next_safe_action,
            ]
            + self.runtime_gateway_execution_route_refs
            + self.runtime_gateway_cli_refs
        ):
            validate_safe_task_text(value, "coding_test_command_readiness_text")
        if not self.suggested_commands:
            raise ValueError("test command readiness needs suggested command refs")
        command_refs = {item.command_ref for item in self.suggested_commands}
        if len(command_refs) != len(self.suggested_commands):
            raise ValueError("test command readiness command refs must be unique")
        expected_refs = {item.expected_receipt_ref for item in self.suggested_commands}
        if set(self.expected_receipt_refs) != expected_refs:
            raise ValueError("expected receipt refs must match suggested commands")
        allowlist_refs = {item.allowlist_ref for item in self.suggested_commands}
        if set(self.allowlist_refs) != allowlist_refs:
            raise ValueError("allowlist refs must match suggested commands")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "readiness_only": self.readiness_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding test command readiness disabled {disabled[0]}")
        if self.status == "approval_required_runtime_lane_available":
            required_lane_flags = {
                "approval_required": self.approval_required,
                "exact_runtime_lane_available": self.exact_runtime_lane_available,
                "runtime_gateway_receipts_available": (
                    self.runtime_gateway_receipts_available
                ),
            }
            disabled_lane_flags = [
                name for name, value in required_lane_flags.items() if not value
            ]
            if disabled_lane_flags:
                raise ValueError(
                    f"coding test command runtime lane disabled {disabled_lane_flags[0]}"
                )
        required_false_flags = {
            "raw_command_included": self.raw_command_included,
            "raw_output_included": self.raw_output_included,
            "command_output_summary_included": self.command_output_summary_included,
            "exit_code_available": self.exit_code_available,
            "test_receipt_created": self.test_receipt_created,
            "command_execution_enabled": self.command_execution_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "arbitrary_shell_enabled": self.arbitrary_shell_enabled,
            "install_command_enabled": self.install_command_enabled,
            "network_command_enabled": self.network_command_enabled,
            "destructive_command_enabled": self.destructive_command_enabled,
            "background_process_enabled": self.background_process_enabled,
            "file_write_enabled": self.file_write_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding test command readiness enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_test_command_readiness")
        return self


class CodingGitReviewItemReadModel(BaseModel):
    item_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    item_kind: GitReviewItemKind
    status: Literal["blocked", "proposal_ref"]
    safe_summary: str = Field(..., min_length=1, max_length=420)
    expected_receipt_ref: str = Field(..., min_length=1)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_git_output_included: bool = False
    raw_diff_included: bool = False
    raw_path_included: bool = False
    git_mutation_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_git_review_item(self) -> "CodingGitReviewItemReadModel":
        for ref in [
            self.item_ref,
            self.expected_receipt_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_git_review_item_ref")
        for value in [
            self.label,
            self.item_kind,
            self.status,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "coding_git_review_item_text")
        if not self.blocked_authority_refs:
            raise ValueError("git review item needs blocker refs")
        required_false_flags = {
            "raw_git_output_included": self.raw_git_output_included,
            "raw_diff_included": self.raw_diff_included,
            "raw_path_included": self.raw_path_included,
            "git_mutation_enabled": self.git_mutation_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding git review item enabled {enabled[0]}")
        return self


class CodingGitReviewReadModel(BaseModel):
    schema_version: Literal["uaa-coding-git-review.v1"] = "uaa-coding-git-review.v1"
    git_review_ref: str = CODING_COCKPIT_GIT_REVIEW_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    patch_apply_readiness_ref: str = CODING_COCKPIT_PATCH_APPLY_READINESS_REF
    test_command_readiness_ref: str = CODING_COCKPIT_TEST_COMMAND_READINESS_REF
    route_ref: str = CODING_COCKPIT_GIT_REVIEW_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_GIT_REVIEW_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-git-review"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:coding-git-review-blocker",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    unblock_prompt_refs: list[str] = Field(
        default_factory=lambda: ["prompt-ref:unblock-coding-git-review"]
    )
    status: GitReviewStatus = "blocked_missing_git_review_authority"
    title: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    status_refs: list[str] = Field(default_factory=list)
    changed_file_refs: list[str] = Field(default_factory=list)
    diff_refs: list[str] = Field(default_factory=list)
    commit_proposal_refs: list[str] = Field(default_factory=list)
    pr_description_proposal_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    review_items: list[CodingGitReviewItemReadModel] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    proposal_only: bool = True
    safe_refs_only: bool = True
    git_status_execution_enabled: bool = False
    git_diff_execution_enabled: bool = False
    stage_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    pr_open_enabled: bool = False
    merge_enabled: bool = False
    raw_git_output_included: bool = False
    raw_diff_included: bool = False
    raw_path_included: bool = False
    commit_message_text_included: bool = False
    pr_description_text_included: bool = False
    git_receipt_created: bool = False
    shell_subprocess_execution_enabled: bool = False
    file_write_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_git_review(self) -> "CodingGitReviewReadModel":
        for ref in [
            self.git_review_ref,
            self.session_ref,
            self.context_pack_ref,
            self.patch_proposal_ref,
            self.patch_apply_readiness_ref,
            self.test_command_readiness_ref,
            self.route_ref,
            *self.status_refs,
            *self.changed_file_refs,
            *self.diff_refs,
            *self.commit_proposal_refs,
            *self.pr_description_proposal_refs,
            *self.expected_receipt_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_git_review_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.title,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_git_review_text")
        if not self.review_items:
            raise ValueError("git review needs item refs")
        item_refs = {item.item_ref for item in self.review_items}
        if len(item_refs) != len(self.review_items):
            raise ValueError("git review item refs must be unique")
        expected_refs = {item.expected_receipt_ref for item in self.review_items}
        if set(self.expected_receipt_refs) != expected_refs:
            raise ValueError("git expected receipt refs must match review items")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "proposal_only": self.proposal_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding git review disabled {disabled[0]}")
        required_false_flags = {
            "git_status_execution_enabled": self.git_status_execution_enabled,
            "git_diff_execution_enabled": self.git_diff_execution_enabled,
            "stage_enabled": self.stage_enabled,
            "commit_enabled": self.commit_enabled,
            "push_enabled": self.push_enabled,
            "pr_open_enabled": self.pr_open_enabled,
            "merge_enabled": self.merge_enabled,
            "raw_git_output_included": self.raw_git_output_included,
            "raw_diff_included": self.raw_diff_included,
            "raw_path_included": self.raw_path_included,
            "commit_message_text_included": self.commit_message_text_included,
            "pr_description_text_included": self.pr_description_text_included,
            "git_receipt_created": self.git_receipt_created,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "file_write_enabled": self.file_write_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding git review enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_git_review")
        return self


class CodingLivePreviewItemReadModel(BaseModel):
    item_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    item_kind: LivePreviewItemKind
    status: Literal["blocked", "planned", "proposal_ref"]
    safe_summary: str = Field(..., min_length=1, max_length=420)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_url_included: bool = False
    screenshot_included: bool = False
    console_output_included: bool = False
    browser_automation_enabled: bool = False
    dev_server_control_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_live_preview_item(self) -> "CodingLivePreviewItemReadModel":
        for ref in [
            self.item_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_live_preview_item_ref")
        for value in [
            self.label,
            self.item_kind,
            self.status,
            self.safe_summary,
        ]:
            validate_safe_task_text(value, "coding_live_preview_item_text")
        if not self.blocked_authority_refs:
            raise ValueError("live preview item needs blocker refs")
        required_false_flags = {
            "raw_url_included": self.raw_url_included,
            "screenshot_included": self.screenshot_included,
            "console_output_included": self.console_output_included,
            "browser_automation_enabled": self.browser_automation_enabled,
            "dev_server_control_enabled": self.dev_server_control_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding live preview item enabled {enabled[0]}")
        return self


class CodingLivePreviewReadModel(BaseModel):
    schema_version: Literal["uaa-coding-live-preview.v1"] = (
        "uaa-coding-live-preview.v1"
    )
    live_preview_ref: str = CODING_COCKPIT_LIVE_PREVIEW_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    test_command_readiness_ref: str = CODING_COCKPIT_TEST_COMMAND_READINESS_REF
    git_review_ref: str = CODING_COCKPIT_GIT_REVIEW_REF
    route_ref: str = CODING_COCKPIT_LIVE_PREVIEW_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_LIVE_PREVIEW_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: ["scripts/dev/uaa_coding.py inspect-live-preview"]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:coding-live-preview-blocker",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    unblock_prompt_refs: list[str] = Field(
        default_factory=lambda: ["prompt-ref:unblock-coding-live-preview"]
    )
    status: LivePreviewStatus = "blocked_missing_live_preview_authority"
    title: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    dev_server_status_refs: list[str] = Field(default_factory=list)
    preview_url_refs: list[str] = Field(default_factory=list)
    screenshot_refs: list[str] = Field(default_factory=list)
    visual_proof_refs: list[str] = Field(default_factory=list)
    route_checklist_refs: list[str] = Field(default_factory=list)
    viewport_refs: list[str] = Field(default_factory=list)
    console_error_refs: list[str] = Field(default_factory=list)
    preview_items: list[CodingLivePreviewItemReadModel] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    status_only: bool = True
    safe_refs_only: bool = True
    raw_url_included: bool = False
    raw_console_output_included: bool = False
    screenshot_artifact_included: bool = False
    screenshot_capture_enabled: bool = False
    visual_regression_enabled: bool = False
    console_capture_enabled: bool = False
    dev_server_status_detection_enabled: bool = False
    dev_server_start_enabled: bool = False
    dev_server_stop_enabled: bool = False
    browser_preview_enabled: bool = False
    browser_automation_enabled: bool = False
    browser_interaction_enabled: bool = False
    network_fetch_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    file_write_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_live_preview(self) -> "CodingLivePreviewReadModel":
        for ref in [
            self.live_preview_ref,
            self.session_ref,
            self.context_pack_ref,
            self.patch_proposal_ref,
            self.test_command_readiness_ref,
            self.git_review_ref,
            self.route_ref,
            *self.dev_server_status_refs,
            *self.preview_url_refs,
            *self.screenshot_refs,
            *self.visual_proof_refs,
            *self.route_checklist_refs,
            *self.viewport_refs,
            *self.console_error_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_live_preview_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.title,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_live_preview_text")
        if not self.preview_items:
            raise ValueError("live preview needs item refs")
        item_refs = {item.item_ref for item in self.preview_items}
        if len(item_refs) != len(self.preview_items):
            raise ValueError("live preview item refs must be unique")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "status_only": self.status_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding live preview disabled {disabled[0]}")
        required_false_flags = {
            "raw_url_included": self.raw_url_included,
            "raw_console_output_included": self.raw_console_output_included,
            "screenshot_artifact_included": self.screenshot_artifact_included,
            "screenshot_capture_enabled": self.screenshot_capture_enabled,
            "visual_regression_enabled": self.visual_regression_enabled,
            "console_capture_enabled": self.console_capture_enabled,
            "dev_server_status_detection_enabled": (
                self.dev_server_status_detection_enabled
            ),
            "dev_server_start_enabled": self.dev_server_start_enabled,
            "dev_server_stop_enabled": self.dev_server_stop_enabled,
            "browser_preview_enabled": self.browser_preview_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "browser_interaction_enabled": self.browser_interaction_enabled,
            "network_fetch_enabled": self.network_fetch_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "file_write_enabled": self.file_write_enabled,
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding live preview enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_live_preview")
        return self


class CodingAgentReviewSlotReadModel(BaseModel):
    agent_slot_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    slot_kind: AgentReviewSlotKind
    status: Literal["proposal_ref", "blocked"]
    safe_summary: str = Field(..., min_length=1, max_length=420)
    output_artifact_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    provider_model_call_enabled: bool = False
    local_agent_execution_enabled: bool = False
    background_dispatch_enabled: bool = False
    autonomous_execution_enabled: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_agent_review_slot(self) -> "CodingAgentReviewSlotReadModel":
        for ref in [
            self.agent_slot_ref,
            *self.output_artifact_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
        ]:
            validate_task_ref(ref, "coding_agent_review_slot_ref")
        for value in [self.label, self.slot_kind, self.status, self.safe_summary]:
            validate_safe_task_text(value, "coding_agent_review_slot_text")
        if not self.blocked_authority_refs:
            raise ValueError("agent review slot needs blocker refs")
        required_false_flags = {
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "local_agent_execution_enabled": self.local_agent_execution_enabled,
            "background_dispatch_enabled": self.background_dispatch_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "raw_prompt_included": self.raw_prompt_included,
            "raw_response_included": self.raw_response_included,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding agent review slot enabled {enabled[0]}")
        return self


class CodingMultiAgentReviewReadModel(BaseModel):
    schema_version: Literal["uaa-coding-multi-agent-review.v1"] = (
        "uaa-coding-multi-agent-review.v1"
    )
    review_ref: str = CODING_COCKPIT_MULTI_AGENT_REVIEW_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    test_command_readiness_ref: str = CODING_COCKPIT_TEST_COMMAND_READINESS_REF
    git_review_ref: str = CODING_COCKPIT_GIT_REVIEW_REF
    live_preview_ref: str = CODING_COCKPIT_LIVE_PREVIEW_REF
    route_ref: str = CODING_COCKPIT_MULTI_AGENT_REVIEW_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_MULTI_AGENT_REVIEW_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_coding.py inspect-multi-agent-review"
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:governed-code-workbench",
            "docs-ref:coding-multi-agent-review-blocker",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    unblock_prompt_refs: list[str] = Field(
        default_factory=lambda: ["prompt-ref:unblock-coding-multi-agent-review"]
    )
    status: MultiAgentReviewStatus = "blocked_missing_multi_agent_authority"
    title: str = Field(..., min_length=1, max_length=120)
    full_strength_goal: str = Field(..., min_length=1, max_length=520)
    repo_safe_current_state: str = Field(..., min_length=1, max_length=520)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    agent_slots: list[CodingAgentReviewSlotReadModel] = Field(default_factory=list)
    plan_artifact_refs: list[str] = Field(default_factory=list)
    review_artifact_refs: list[str] = Field(default_factory=list)
    diff_comparison_refs: list[str] = Field(default_factory=list)
    disagreement_summary_refs: list[str] = Field(default_factory=list)
    handoff_refs: list[str] = Field(default_factory=list)
    pair_agent_relay: CodingPairAgentRelayReadModel
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    proposal_only: bool = True
    safe_refs_only: bool = True
    provider_model_call_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    local_agent_execution_enabled: bool = False
    multi_agent_execution_enabled: bool = False
    background_dispatch_enabled: bool = False
    background_autonomy_enabled: bool = False
    autonomous_execution_enabled: bool = False
    context_injection_enabled: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    provider_payload_included: bool = False
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_multi_agent_review(self) -> "CodingMultiAgentReviewReadModel":
        for ref in [
            self.review_ref,
            self.session_ref,
            self.context_pack_ref,
            self.patch_proposal_ref,
            self.test_command_readiness_ref,
            self.git_review_ref,
            self.live_preview_ref,
            self.route_ref,
            *self.plan_artifact_refs,
            *self.review_artifact_refs,
            *self.diff_comparison_refs,
            *self.disagreement_summary_refs,
            *self.handoff_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
            *self.docs_refs,
            *self.unblock_prompt_refs,
        ]:
            validate_task_ref(ref, "coding_multi_agent_review_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.title,
                self.full_strength_goal,
                self.repo_safe_current_state,
                self.safe_summary,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_multi_agent_review_text")
        if not self.agent_slots:
            raise ValueError("multi-agent review needs agent slots")
        slot_refs = {item.agent_slot_ref for item in self.agent_slots}
        if len(slot_refs) != len(self.agent_slots):
            raise ValueError("multi-agent slot refs must be unique")
        if (
            self.pair_agent_relay.lane_ref
            != "coding-pair-agent-lane:coding_pair_agent_foreground_relay_runner"
        ):
            raise ValueError("multi-agent review needs pair relay lane ref")
        if self.pair_agent_relay.execution_promoted:
            raise ValueError("pair relay execution cannot be promoted here")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "proposal_only": self.proposal_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding multi-agent review disabled {disabled[0]}")
        required_false_flags = {
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "local_agent_execution_enabled": self.local_agent_execution_enabled,
            "multi_agent_execution_enabled": self.multi_agent_execution_enabled,
            "background_dispatch_enabled": self.background_dispatch_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "autonomous_execution_enabled": self.autonomous_execution_enabled,
            "context_injection_enabled": self.context_injection_enabled,
            "raw_prompt_included": self.raw_prompt_included,
            "raw_response_included": self.raw_response_included,
            "provider_payload_included": self.provider_payload_included,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding multi-agent review enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_multi_agent_review")
        return self


class CodingCockpitSessionReadModel(BaseModel):
    schema_version: Literal["uaa-coding-cockpit-session.v1"] = (
        "uaa-coding-cockpit-session.v1"
    )
    contract_ref: str = CODING_COCKPIT_CONTRACT_REF
    route_ref: str = CODING_COCKPIT_ROUTE_REF
    session_ref: str = CODING_COCKPIT_SESSION_REF
    workspace_ref: str = "workspace-ref:coding:local-uaa"
    repo_scope_ref: str = "repo-scope:coding:local-uaa"
    branch_ref: str = "branch-ref:coding:current-local"
    authority_profile_ref: str = "authority-profile:coding:read-only"
    active_agent_ref: str = "agent-ref:coding:codex-slot"
    active_task_ref: str = "coding-task:cockpit-shell-seed"
    active_context_pack_ref: str = CODING_COCKPIT_CONTEXT_PACK_REF
    active_patch_proposal_ref: str = CODING_COCKPIT_PATCH_PROPOSAL_REF
    active_command_proposal_ref: str = "command-proposal:coding-blocked-seed"
    active_git_ref: str = CODING_COCKPIT_GIT_REVIEW_REF
    active_proof_ref: str = "proof-ref:coding-cockpit-seed"
    active_preview_ref: str = CODING_COCKPIT_LIVE_PREVIEW_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [CODING_COCKPIT_FRONTEND_ROUTE_REF]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:control-center-coding-cockpit",
            "docs-ref:operator-shell-gap-map",
        ]
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_coding.py inspect-session",
            "scripts/dev/uaa_coding.py inspect-project-model",
            "scripts/dev/uaa_coding.py inspect-context",
            "scripts/dev/uaa_coding.py inspect-patch-proposal",
            "scripts/dev/uaa_coding.py inspect-patch-apply-readiness",
            "scripts/dev/uaa_coding.py inspect-test-command-readiness",
            "scripts/dev/uaa_coding.py inspect-git-review",
            "scripts/dev/uaa_coding.py inspect-live-preview",
            "scripts/dev/uaa_coding.py inspect-multi-agent-review",
        ]
    )
    status: str = "implemented_read_only_cockpit_seed"
    task_status: CockpitTaskStatus = "read_only_seed"
    branch_label: str = "current local branch ref"
    active_agent_label: str = "Codex slot, read-only seed"
    authority_mode: str = "Read Only"
    backend_owned: bool = True
    mock_fallback: bool = False
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    control_center_grants_authority: bool = False
    full_strength_goal: str = Field(
        default=(
            "Local coding cockpit for chat, context, diff, terminal, Git, "
            "preview, proof, and multi-agent review."
        ),
        min_length=1,
        max_length=300,
    )
    repo_safe_scope: str = Field(
        default=(
            "Prompt 01 seed renders backend-owned read-only cockpit state with "
            "proposal placeholders and blocked runtime lanes."
        ),
        min_length=1,
        max_length=300,
    )
    authority_modes: list[CodingCockpitAuthorityMode] = Field(default_factory=list)
    project_model: CodingProjectModelReadModel
    workspace_context: CodingCockpitPreviewPanel
    task_thread: CodingCockpitPreviewPanel
    task_timeline: CodingCockpitPreviewPanel
    diff_preview: CodingCockpitPreviewPanel
    proof_preview: CodingCockpitPreviewPanel
    terminal_preview: CodingCockpitPreviewPanel
    git_preview: CodingCockpitPreviewPanel
    test_output_preview: CodingCockpitPreviewPanel
    live_preview: CodingCockpitPreviewPanel
    chat_thread: CodingCockpitPreviewPanel
    same_ref_spine: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    file_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_automation_enabled: bool = False
    connector_write_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_session(self) -> "CodingCockpitSessionReadModel":
        for field_name in [
            "contract_ref",
            "route_ref",
            "session_ref",
            "workspace_ref",
            "repo_scope_ref",
            "branch_ref",
            "authority_profile_ref",
            "active_agent_ref",
            "active_task_ref",
            "active_context_pack_ref",
            "active_patch_proposal_ref",
            "active_command_proposal_ref",
            "active_git_ref",
            "active_proof_ref",
            "active_preview_ref",
        ]:
            validate_task_ref(getattr(self, field_name), field_name)
        for ref in (
            self.same_ref_spine
            + self.blocked_authority_refs
            + self.promotion_path_refs
            + self.redactions_applied
            + self.docs_refs
        ):
            validate_task_ref(ref, "coding_session_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.status,
                self.task_status,
                self.branch_label,
                self.active_agent_label,
                self.authority_mode,
                self.full_strength_goal,
                self.repo_safe_scope,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "coding_session_text")
        missing = set(CODING_COCKPIT_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        )
        if missing:
            raise ValueError("coding cockpit session missing blocked refs")
        if self.project_model.project_model_ref not in self.same_ref_spine:
            raise ValueError("coding cockpit session missing project model ref spine")
        if self.project_model.session_ref != self.session_ref:
            raise ValueError("coding cockpit session project model ref mismatch")
        required_false_flags = {
            "raw_content_included": self.raw_content_included,
            "control_center_grants_authority": self.control_center_grants_authority,
            "file_write_enabled": self.file_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "git_mutation_enabled": self.git_mutation_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in required_false_flags.items() if value]
        if enabled:
            raise ValueError(f"coding cockpit enabled {enabled[0]}")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "local_read_model_only": self.local_read_model_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"coding cockpit disabled {disabled[0]}")
        payload = self.model_dump(mode="json")
        validate_safe_task_payload(payload, "coding_cockpit_session")
        return self


def build_coding_project_model_read_model() -> CodingProjectModelReadModel:
    evidence_refs = ["evidence-ref:coding-project-model-read-model"]
    proof_refs = ["proof-ref:coding-project-model"]
    blocked_refs = [
        "blocked-state:coding-no-file-write",
        "blocked-state:coding-no-shell-subprocess",
        "blocked-state:coding-no-git-mutation",
        "blocked-state:coding-no-browser-automation",
        "blocked-state:coding-no-provider-model-call",
        "blocked-state:coding-no-background-autonomy",
        "blocked-state:coding-no-production-authority",
    ]
    capabilities = [
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:workspace-ref-spine",
            label="Workspace ref spine",
            capability_kind="workspace",
            state="read_only",
            safe_summary=(
                "Workspace identity is shown as safe refs and does not reveal a "
                "local path."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            promotion_path_refs=["promotion-path:coding-workspace-safe-refs"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:repo-scope",
            label="Repository scope",
            capability_kind="repo",
            state="read_only",
            safe_summary=(
                "Repo scope is visible as a local project ref without scanning files."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            promotion_path_refs=["promotion-path:coding-context-pack-preview"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:project-lane",
            label="Coding lane posture",
            capability_kind="lane",
            state="read_only",
            safe_summary=(
                "Coding lane binds context, patch, tests, preview, Git, and proof "
                "refs into one project posture."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            promotion_path_refs=["promotion-path:coding-project-lane-proof"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:branch-posture",
            label="Branch posture",
            capability_kind="branch",
            state="read_only",
            safe_summary=(
                "Branch posture is display-only and does not run Git status."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-git-status-reader"],
            promotion_path_refs=["promotion-path:coding-git-review-lane"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:worktree-posture",
            label="Worktree posture",
            capability_kind="worktree",
            state="read_only",
            safe_summary=(
                "Worktree posture is a safe ref only; no local path or file scan "
                "is included."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-project-scan"],
            promotion_path_refs=["promotion-path:coding-worktree-safe-reader"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:file-refs",
            label="File refs",
            capability_kind="files",
            state="proposal_only",
            safe_summary=(
                "Files are represented by context and patch refs without raw paths "
                "or raw content."
            ),
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-file-write"],
            promotion_path_refs=["promotion-path:coding-context-pack-preview"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:diff-refs",
            label="Diff refs",
            capability_kind="diffs",
            state="proposal_only",
            safe_summary=(
                "Diff posture uses patch and hunk refs only; no raw diff body or "
                "apply authority is available."
            ),
            source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-patch-apply",
                "blocked-state:coding-no-file-write",
            ],
            promotion_path_refs=["promotion-path:coding-patch-proposal-lane"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:test-lane",
            label="Test lane",
            capability_kind="tests",
            state="read_only",
            safe_summary=(
                "Test posture shows approval-required RuntimeGateway validation "
                "refs; execution still requires a separate Action Inbox approval "
                "and RuntimeGateway receipt."
            ),
            source_refs=[CODING_COCKPIT_TEST_COMMAND_READINESS_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-arbitrary-shell",
                "blocked-state:coding-no-network-command",
            ],
            promotion_path_refs=["promotion-path:coding-validation-runtime-lane"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:preview-lane",
            label="Live preview lane",
            capability_kind="preview",
            state="blocked",
            safe_summary=(
                "Preview posture is status-only; dev server control and browser "
                "preview remain unavailable."
            ),
            source_refs=[CODING_COCKPIT_LIVE_PREVIEW_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-browser-automation",
                "blocked-state:coding-no-dev-server-control",
            ],
            promotion_path_refs=["promotion-path:coding-live-preview-status"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:terminal-lane",
            label="Terminal lane",
            capability_kind="terminal",
            state="blocked",
            safe_summary=(
                "Terminal posture is read-only readiness; no subprocess or "
                "interactive terminal is enabled."
            ),
            source_refs=[CODING_COCKPIT_TEST_COMMAND_READINESS_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-command-execution",
            ],
            promotion_path_refs=["promotion-path:coding-terminal-controls-blocked"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:git-lane",
            label="Git lane",
            capability_kind="git",
            state="blocked",
            safe_summary=(
                "Git posture shows review refs only; status execution, stage, "
                "commit, push, and PR actions are unavailable."
            ),
            source_refs=[CODING_COCKPIT_GIT_REVIEW_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-git-status-reader",
                "blocked-state:coding-no-git-mutation",
            ],
            promotion_path_refs=["promotion-path:coding-git-review-lane"],
        ),
        CodingProjectCapabilityReadModel(
            capability_ref="coding-project-capability:proof-spine",
            label="Proof spine",
            capability_kind="proof",
            state="read_only",
            safe_summary=(
                "Proof posture binds project, task, context, patch, command, Git, "
                "preview, and multi-agent refs."
            ),
            source_refs=[CODING_COCKPIT_SESSION_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            promotion_path_refs=["promotion-path:coding-proof-detail"],
        ),
    ]
    return CodingProjectModelReadModel(
        project_label="Local UAA coding project",
        repo_label="Local repository safe ref",
        branch_label="Current branch safe ref",
        worktree_label="Current worktree safe ref",
        full_strength_goal=(
            "UAA Coding Cockpit supports projects, repos, lanes, branches, "
            "worktrees, files, diffs, tests, preview, terminal, Git, and proof "
            "as one governed coding command center."
        ),
        repo_safe_current_state=(
            "Phase 21 adds backend-owned project posture only. It does not read "
            "repo files, scan local paths, run commands, run Git, open browsers, "
            "call providers, or dispatch coding agents."
        ),
        safe_summary=(
            "Project posture ties the coding cockpit lanes together through safe "
            "refs while keeping all runtime and mutation authority blocked."
        ),
        capabilities=capabilities,
        capability_refs=[item.capability_ref for item in capabilities],
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path:coding-context-pack-preview",
            "promotion-path:coding-patch-proposal-lane",
            "promotion-path:coding-approved-apply-lane",
            "promotion-path:coding-validation-runtime-lane",
            "promotion-path:coding-git-review-lane",
            "promotion-path:coding-live-preview-status",
            "promotion-path:coding-multi-agent-review",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:bounded-summaries-only",
        ],
        next_safe_action=(
            "Use this project posture to review coding lanes before promoting "
            "exact context, patch, test, Git, preview, or agent authority."
        ),
    )


def build_coding_cockpit_session_seed() -> CodingCockpitSessionReadModel:
    blocked = list(CODING_COCKPIT_REQUIRED_BLOCKED_REFS)
    proof_refs = ["proof-ref:coding-cockpit-seed"]
    evidence_refs = ["evidence-ref:coding-cockpit-read-model"]
    return CodingCockpitSessionReadModel(
        authority_modes=[
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-read-only",
                label="Read Only",
                state="current",
                operator_posture="Inspect, search, plan, and compose context refs.",
                safe_summary=(
                    "Current session may show repo and task posture through safe "
                    "refs only."
                ),
                allowed_now=True,
                planned=False,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-context-pack-preview"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-ask-before-changes",
                label="Ask Before Changes",
                state="planned",
                operator_posture="Proposal lane before exact approved mutation.",
                safe_summary=(
                    "Future session mode may prepare exact patch proposals for "
                    "operator review."
                ),
                allowed_now=False,
                planned=True,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-patch-proposal-lane"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-safe-local-work",
                label="Approve Safe Local Work For Me",
                state="planned",
                operator_posture="Session-scoped safe local lane after verifiers.",
                safe_summary=(
                    "Future scoped mode requires allowlisted edits, receipts, "
                    "and rollback posture before enablement."
                ),
                allowed_now=False,
                planned=True,
                blocked=False,
                blocked_authority_refs=[],
                promotion_path_refs=["promotion-path:coding-approved-apply-lane"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-full-local-workspace",
                label="Full Local Workspace Access",
                state="blocked",
                operator_posture="Broad local repo authority is not granted.",
                safe_summary=(
                    "Broad editing and local command lanes require separate "
                    "receipts, rollback posture, and verifier gates."
                ),
                allowed_now=False,
                planned=False,
                blocked=True,
                blocked_authority_refs=[
                    "blocked-state:coding-no-file-write",
                    "blocked-state:coding-no-shell-subprocess",
                    "blocked-state:coding-no-git-mutation",
                ],
                promotion_path_refs=["promotion-path:coding-approved-local-work"],
            ),
            CodingCockpitAuthorityMode(
                mode_ref="authority-mode:coding-external-production",
                label="External / Production Authority",
                state="hard_gate",
                operator_posture="External write and production lanes are separate.",
                safe_summary=(
                    "External side effects require a separate authority gate and "
                    "cannot be bundled with the coding cockpit."
                ),
                allowed_now=False,
                planned=False,
                blocked=True,
                blocked_authority_refs=[
                    "blocked-state:coding-no-connector-write",
                    "blocked-state:coding-no-production-authority",
                ],
                promotion_path_refs=["promotion-path:external-production-gate"],
            ),
        ],
        project_model=build_coding_project_model_read_model(),
        workspace_context=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:workspace-context",
            title="Workspace Context",
            state="backend_owned",
            safe_summary=(
                "Workspace panel renders the Prompt 02 context-pack preview with "
                "pinned refs, excluded noisy refs, and budget posture."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="context-item:coding-pinned-files",
                    label="Pinned refs",
                    status="read-only preview",
                    safe_summary="Operator-selected safe refs are visible without raw paths.",
                    source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                ),
                CodingCockpitRefItem(
                    item_ref="context-item:coding-excluded-noise",
                    label="Excluded refs",
                    status="read-only preview",
                    safe_summary="Generated and noisy path filters are visible as refs only.",
                    source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[],
                ),
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-file-write"],
            next_safe_action="Inspect safe context refs before any patch proposal lane.",
        ),
        task_thread=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:task-thread",
            title="Coding Task",
            state="read_only",
            safe_summary=(
                "Active task seed links plan, context, patch proposal, command "
                "proposal, Git posture, and proof refs."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="coding-task:cockpit-shell-seed",
                    label="Prompt 01 cockpit shell",
                    status="read-only seed",
                    safe_summary="Render the cockpit shell and read model seed only.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=blocked,
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=blocked,
            next_safe_action="Review the seeded read model before later proposal lanes.",
        ),
        task_timeline=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:timeline",
            title="Workflow Timeline",
            state="read_only",
            safe_summary=(
                "Timeline shows planned agent workflow checkpoints as safe refs; "
                "no background autonomy is enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="timeline-item:coding-context-selected",
                    label="Context refs selected",
                    status="seeded",
                    safe_summary="Context pack preview is available as safe refs only.",
                    source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[],
                ),
                CodingCockpitRefItem(
                    item_ref="timeline-item:coding-patch-blocked",
                    label="Patch lane",
                    status="proposal artifact ready",
                    safe_summary=(
                        "Patch proposal artifact is inspectable as safe refs; "
                        "apply remains unavailable."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                ),
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_PATCH_APPLY_READINESS_REF,
                    label="Approved apply lane",
                    status="blocked by Prompt 04 readiness",
                    safe_summary=(
                        "Apply remains blocked until exact patch body, approval "
                        "binding, checkpoint, receipt, and rollback contracts exist."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-patch-apply",
                        "blocked-state:coding-no-file-write",
                    ],
                ),
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_TEST_COMMAND_READINESS_REF,
                    label="Allowlisted test command lane",
                    status="blocked by Prompt 05 readiness",
                    safe_summary=(
                        "Suggested focused test command refs are visible, but no "
                        "shell or subprocess execution is available."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-shell-subprocess",
                        "blocked-state:coding-no-command-execution",
                    ],
                ),
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_GIT_REVIEW_REF,
                    label="Git review lane",
                    status="blocked by Prompt 06 readiness",
                    safe_summary=(
                        "Git status, diff, changed-file, commit proposal, and "
                        "pull-request proposal refs are visible, but no Git command "
                        "or mutation authority is available."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-git-mutation",
                        "blocked-state:coding-no-git-status-reader",
                    ],
                ),
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_LIVE_PREVIEW_REF,
                    label="Live preview lane",
                    status="blocked by Prompt 07 readiness",
                    safe_summary=(
                        "Preview status, URL, screenshot, visual proof, route "
                        "checklist, and viewport refs are visible, but no dev "
                        "server or browser authority is available."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-browser-automation",
                        "blocked-state:coding-no-dev-server-control",
                    ],
                ),
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_MULTI_AGENT_REVIEW_REF,
                    label="Multi-agent review lane",
                    status="blocked by Prompt 08 readiness",
                    safe_summary=(
                        "Codex, Claude, local verifier, security, UX, test fixer, "
                        "and merge captain slots are visible as proposal refs only; "
                        "no agent dispatch or provider call is available."
                    ),
                    source_refs=[CODING_COCKPIT_PATCH_PROPOSAL_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-provider-model-call",
                        "blocked-state:coding-no-background-autonomy",
                    ],
                ),
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-background-autonomy"],
            next_safe_action="Use timeline refs as proof posture only.",
        ),
        diff_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:diff-preview",
            title="Diff Preview",
            state="proposal_only",
            safe_summary=(
                "Patch proposal lane exposes safe diff refs and bounded summaries; "
                "no diff body or apply control is enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_PATCH_PROPOSAL_REF,
                    label="Patch proposal artifact",
                    status="proposal-only",
                    safe_summary=(
                        "File and hunk refs are reviewable without raw paths, raw "
                        "content, or apply authority."
                    ),
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=["blocked-state:coding-no-file-write"],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-file-write"],
            next_safe_action="Review safe patch refs before any future apply lane.",
        ),
        proof_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:proof-preview",
            title="Proof Detail",
            state="backend_owned",
            safe_summary=(
                "Proof preview binds request, plan, context, patch, command, "
                "Git, terminal, and preview refs to one safe spine."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="proof-ref:coding-cockpit-seed",
                    label="Coding cockpit proof",
                    status="seeded",
                    safe_summary="Proof ref records blocked authority and next safe action.",
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=blocked,
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=blocked,
            next_safe_action="Open universal Proof after the proof lane is expanded.",
        ),
        terminal_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:terminal-preview",
            title="Terminal Preview",
            state="blocked",
            safe_summary=(
                "Terminal panel shows Prompt 05 suggested test command refs only; "
                "local command running remains blocked."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_TEST_COMMAND_READINESS_REF,
                    label="Allowlisted test command readiness",
                    status="blocked",
                    safe_summary=(
                        "Focused pytest, frontend test, lint/typecheck, and "
                        "verifier command refs are proposed without raw commands."
                    ),
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-shell-subprocess",
                        "blocked-state:coding-no-command-execution",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-command-execution",
            ],
            next_safe_action=(
                "Keep command controls disabled until an implemented workspace/shell "
                "AuthorityLease scope, exact approval, receipts, and safe-disable "
                "posture are present."
            ),
        ),
        git_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:git-preview",
            title="Git Preview",
            state="preview_only",
            safe_summary=(
                "Git panel shows Prompt 06 review refs only; live status, diff, "
                "stage, commit, push, and pull-request actions are not enabled."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_GIT_REVIEW_REF,
                    label="Git review readiness",
                    status="blocked",
                    safe_summary=(
                        "Git status, diff, changed-file, commit proposal, and "
                        "pull-request proposal refs are present without live Git "
                        "output or mutation authority."
                    ),
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-git-mutation",
                        "blocked-state:coding-no-git-status-reader",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-git-mutation",
                "blocked-state:coding-no-git-status-reader",
            ],
            next_safe_action="Inspect Prompt 06 Git review refs before any approved Git lane.",
        ),
        test_output_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:test-output-preview",
            title="Test Output",
            state="planned",
            safe_summary=(
                "Test output lane shows expected receipt refs only; no test "
                "runner output or exit code is available."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref="test-receipt:coding-allowlisted-tests-required",
                    label="Expected test receipt",
                    status="blocked",
                    safe_summary=(
                        "A redacted test receipt is required before UAA can claim "
                        "test execution evidence."
                    ),
                    source_refs=[CODING_COCKPIT_TEST_COMMAND_READINESS_REF],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-shell-subprocess",
                        "blocked-state:coding-no-test-receipt",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-test-receipt",
            ],
            next_safe_action="Inspect Prompt 05 readiness before promoting command execution.",
        ),
        live_preview=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:live-preview",
            title="Live Preview",
            state="blocked",
            safe_summary=(
                "Live preview panel shows Prompt 07 status refs only; browser "
                "automation, dev server control, screenshots, and console capture "
                "are not available."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_LIVE_PREVIEW_REF,
                    label="Live preview readiness",
                    status="blocked",
                    safe_summary=(
                        "Dev server status, preview URL, screenshot, visual proof, "
                        "route checklist, and viewport refs are present without "
                        "runtime preview authority."
                    ),
                    source_refs=["coding-session:local-readonly-cockpit"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-browser-automation",
                        "blocked-state:coding-no-shell-subprocess",
                        "blocked-state:coding-no-dev-server-control",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-browser-automation",
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-dev-server-control",
            ],
            next_safe_action="Inspect Prompt 07 live preview refs before any browser interaction lane.",
        ),
        chat_thread=CodingCockpitPreviewPanel(
            panel_ref="coding-panel:chat-thread",
            title="Agent Thread",
            state="proposal_only",
            safe_summary=(
                "Chat lane displays Prompt 08 multi-agent review refs, but does "
                "not call models, dispatch agents, or run local reviewers."
            ),
            items=[
                CodingCockpitRefItem(
                    item_ref=CODING_COCKPIT_MULTI_AGENT_REVIEW_REF,
                    label="Multi-agent review readiness",
                    status="blocked",
                    safe_summary=(
                        "Agent slots and comparison refs are visible without "
                        "provider/model calls, raw prompts, raw responses, or "
                        "background dispatch."
                    ),
                    source_refs=["coding-task:cockpit-shell-seed"],
                    evidence_refs=evidence_refs,
                    proof_refs=proof_refs,
                    blocked_authority_refs=[
                        "blocked-state:coding-no-provider-model-call",
                        "blocked-state:coding-no-background-autonomy",
                    ],
                )
            ],
            proof_refs=proof_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-background-autonomy",
            ],
            next_safe_action="Keep chat as task-thread presentation until provider authority is scoped.",
        ),
        same_ref_spine=[
            "coding-session:local-readonly-cockpit",
            CODING_COCKPIT_PROJECT_MODEL_REF,
            "coding-task:cockpit-shell-seed",
            CODING_COCKPIT_CONTEXT_PACK_REF,
            CODING_COCKPIT_PATCH_PROPOSAL_REF,
            CODING_COCKPIT_PATCH_APPLY_READINESS_REF,
            CODING_COCKPIT_TEST_COMMAND_READINESS_REF,
            "command-proposal:coding-blocked-seed",
            CODING_COCKPIT_GIT_REVIEW_REF,
            CODING_COCKPIT_LIVE_PREVIEW_REF,
            CODING_COCKPIT_MULTI_AGENT_REVIEW_REF,
            "proof-ref:coding-cockpit-seed",
        ],
        blocked_authority_refs=blocked,
        promotion_path_refs=[
            "promotion-path:coding-context-pack-preview",
            "promotion-path:coding-patch-proposal-lane",
            "promotion-path:coding-approved-apply-lane",
            "promotion-path:coding-validation-runtime-lane",
            "promotion-path:coding-git-review-lane",
            "promotion-path:coding-live-preview-status",
            "promotion-path:coding-multi-agent-review",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:bounded-summaries-only",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:raw-paths-omitted",
        ],
        next_safe_action=(
            "Review the read-only cockpit shell and promote Prompt 02 contracts "
            "before adding proposal artifacts."
        ),
    )


def build_coding_workspace_context_preview() -> CodingWorkspaceContextReadModel:
    proof_refs = ["proof-ref:coding-context-pack-preview"]
    evidence_refs = ["evidence-ref:coding-context-pack-read-model"]
    blocked = [
        "blocked-state:coding-no-file-write",
        "blocked-state:coding-no-shell-subprocess",
        "blocked-state:coding-no-provider-model-call",
        "blocked-state:coding-no-production-authority",
    ]
    context_refs = [
        CodingContextRefReadModel(
            context_ref="context-ref:coding-core-contract",
            label="Core coding contract",
            ref_kind="file",
            status="included",
            include_reason=(
                "Defines the backend-owned session and context-pack read model "
                "contracts."
            ),
            token_estimate=4200,
            operator_selected=True,
            agent_selected=True,
            included_in_preview=True,
            safe_summary="Safe ref for the Python Core coding cockpit contract.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[],
        ),
        CodingContextRefReadModel(
            context_ref="context-ref:coding-control-center-panel",
            label="Control Center coding panel",
            ref_kind="file",
            status="included",
            include_reason=(
                "Shows how the cockpit renders workspace, diff, proof, chat, "
                "terminal, Git, test, preview, and authority posture."
            ),
            token_estimate=2800,
            operator_selected=True,
            agent_selected=False,
            included_in_preview=True,
            safe_summary="Safe ref for the Control Center cockpit presentation.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[],
        ),
        CodingContextRefReadModel(
            context_ref="context-ref:coding-api-route-contract",
            label="Coding API route contract",
            ref_kind="file",
            status="included",
            include_reason=(
                "Keeps route, OpenAPI, manifest, and redaction behavior tied to "
                "backend-owned truth."
            ),
            token_estimate=1200,
            operator_selected=False,
            agent_selected=True,
            included_in_preview=True,
            safe_summary="Safe ref for the local coding API read-model route.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[],
        ),
        CodingContextRefReadModel(
            context_ref="context-ref:coding-generated-build-output",
            label="Generated build output",
            ref_kind="exclude_rule",
            status="excluded",
            include_reason=(
                "Generated and noisy material is excluded from coding context "
                "previews by default."
            ),
            token_estimate=0,
            included_in_preview=False,
            excluded_from_preview=True,
            safe_summary="Safe exclude ref; no generated files are persisted.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[],
        ),
        CodingContextRefReadModel(
            context_ref="context-ref:coding-protected-config",
            label="Protected local config",
            ref_kind="exclude_rule",
            status="blocked",
            include_reason=(
                "Protected local configuration material is blocked from context "
                "previews."
            ),
            token_estimate=0,
            included_in_preview=False,
            excluded_from_preview=True,
            safe_summary="Safe exclude ref for protected local config posture.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=["blocked-state:coding-no-protected-context"],
        ),
        CodingContextRefReadModel(
            context_ref="context-ref:coding-search-route-truth",
            label="Route truth search ref",
            ref_kind="search_ref",
            status="candidate",
            include_reason=(
                "Search metadata can suggest route-truth docs without storing "
                "raw query results."
            ),
            token_estimate=0,
            included_in_preview=False,
            safe_summary="Safe search ref for route and proof documentation.",
            source_refs=[CODING_COCKPIT_CONTEXT_PACK_REF],
            evidence_refs=evidence_refs,
            proof_refs=proof_refs,
            blocked_authority_refs=[],
        ),
    ]
    token_estimate_total = sum(
        item.token_estimate for item in context_refs if item.included_in_preview
    )
    return CodingWorkspaceContextReadModel(
        token_estimate_total=token_estimate_total,
        token_budget_remaining=24000 - token_estimate_total,
        context_refs=context_refs,
        operator_selected_refs=[
            "context-ref:coding-core-contract",
            "context-ref:coding-control-center-panel",
        ],
        agent_selected_refs=[
            "context-ref:coding-core-contract",
            "context-ref:coding-api-route-contract",
        ],
        excluded_refs=[
            "context-ref:coding-generated-build-output",
            "context-ref:coding-protected-config",
        ],
        search_refs=["context-ref:coding-search-route-truth"],
        comparison=[
            CodingContextComparisonReadModel(
                comparison_ref="context-comparison:coding-core-aligned",
                label="Core contract alignment",
                operator_context_ref="context-ref:coding-core-contract",
                agent_context_ref="context-ref:coding-core-contract",
                status="aligned",
                safe_summary="Operator and agent context both include the core contract.",
                proof_refs=proof_refs,
            ),
            CodingContextComparisonReadModel(
                comparison_ref="context-comparison:coding-ui-operator-only",
                label="Operator UI emphasis",
                operator_context_ref="context-ref:coding-control-center-panel",
                agent_context_ref="context-ref:coding-api-route-contract",
                status="operator_only",
                safe_summary=(
                    "Operator-selected context emphasizes the cockpit panel; "
                    "agent-selected context emphasizes route binding."
                ),
                proof_refs=proof_refs,
            ),
        ],
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked,
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:protected-context-blocked",
        ],
        next_safe_action=(
            "Review safe context refs and promote patch proposal artifacts "
            "without reading or persisting raw file content."
        ),
    )


def build_coding_patch_proposal_preview() -> CodingPatchProposalReadModel:
    proof_refs = ["proof-ref:coding-patch-proposal-preview"]
    evidence_refs = ["evidence-ref:coding-patch-proposal-read-model"]
    blocked = [
        "blocked-state:coding-no-file-write",
        "blocked-state:coding-no-patch-apply",
        "blocked-state:coding-no-shell-subprocess",
        "blocked-state:coding-no-git-mutation",
        "blocked-state:coding-no-provider-model-call",
        "blocked-state:coding-no-browser-automation",
        "blocked-state:coding-no-production-authority",
    ]
    file_changes = [
        CodingPatchProposalFileReadModel(
            change_ref="patch-change:coding-core-contract-preview",
            file_ref="file-ref:coding-core-contract",
            label="Core read-model contract",
            change_kind="modify",
            status="proposed",
            hunk_refs=[
                "patch-hunk:coding-core-contract-models",
                "patch-hunk:coding-core-contract-builder",
            ],
            additions=64,
            deletions=4,
            safe_summary=(
                "Proposal would add backend-owned patch artifact contracts and "
                "a deterministic safe preview builder."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[],
        ),
        CodingPatchProposalFileReadModel(
            change_ref="patch-change:coding-control-center-preview",
            file_ref="file-ref:coding-control-center-panel",
            label="Control Center patch preview",
            change_kind="modify",
            status="proposed",
            hunk_refs=[
                "patch-hunk:coding-ui-patch-summary",
                "patch-hunk:coding-ui-disabled-apply",
            ],
            additions=38,
            deletions=2,
            safe_summary=(
                "Proposal would render patch file refs, hunk refs, and apply "
                "blocked posture in the cockpit."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=["blocked-state:coding-no-patch-apply"],
        ),
        CodingPatchProposalFileReadModel(
            change_ref="patch-change:coding-generated-output-blocked",
            file_ref="file-ref:coding-generated-output",
            label="Generated output exclusion",
            change_kind="generated_blocked",
            status="blocked",
            hunk_refs=[],
            additions=0,
            deletions=0,
            safe_summary=(
                "Generated output remains excluded from patch proposal preview "
                "and cannot be selected in this lane."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=["blocked-state:coding-no-generated-output"],
        ),
    ]
    return CodingPatchProposalReadModel(
        title="Coding patch proposal preview",
        safe_summary=(
            "Backend-owned proposal artifact over safe file refs and hunk refs; "
            "it is not an apply request and does not contain raw diff content."
        ),
        proposed_file_refs=[
            "file-ref:coding-core-contract",
            "file-ref:coding-control-center-panel",
            "file-ref:coding-generated-output",
        ],
        file_changes=file_changes,
        diff_preview_refs=[
            "patch-hunk:coding-core-contract-models",
            "patch-hunk:coding-core-contract-builder",
            "patch-hunk:coding-ui-patch-summary",
            "patch-hunk:coding-ui-disabled-apply",
        ],
        diff_summary_lines=[
            "Safe hunk refs describe contract and UI preview changes only.",
            "Generated output is blocked from the proposal lane.",
            "Apply remains blocked until an exact approved apply contract exists.",
        ],
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked,
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:diff-body-omitted",
        ],
        next_safe_action=(
            "Review safe patch refs and keep apply blocked until the approved "
            "patch apply lane is scoped."
        ),
    )


def build_coding_patch_apply_readiness() -> CodingPatchApplyReadinessReadModel:
    evidence_refs = ["evidence-ref:coding-patch-apply-readiness"]
    proof_refs = ["proof-ref:coding-patch-apply-readiness"]
    blocked_refs = [
        "blocked-state:coding-no-patch-apply",
        "blocked-state:coding-no-file-write",
        "blocked-state:coding-no-exact-patch-body",
        "blocked-state:coding-no-approval-binding",
        "blocked-state:coding-no-checkpoint-contract",
        "blocked-state:coding-no-rollback-contract",
        "blocked-state:coding-no-sensitive-diff-guard",
    ]
    return CodingPatchApplyReadinessReadModel(
        title="Approved patch apply readiness",
        full_strength_goal=(
            "Apply selected files or hunks from an exact Coding patch proposal "
            "after operator approval, checkpoint creation, receipt emission, and "
            "rollback proof."
        ),
        repo_safe_current_state=(
            "Prompt 04 records a backend-owned readiness and blocker model only. "
            "No patch body is stored, no file is read, and no mutation route exists."
        ),
        safe_summary=(
            "Approved apply is intentionally blocked until Coding has exact patch "
            "body storage, selected-file or hunk scope, approval binding, checkpoint, "
            "rollback, sensitive-data diff blocking, receipt, proof, and CLI parity."
        ),
        required_authority_profile_refs=[
            "authority-profile:coding:ask-before-changes",
            "authority-profile:coding:approve-safe-local-work",
        ],
        prerequisites=[
            CodingPatchApplyPrerequisiteReadModel(
                prerequisite_ref="prereq-ref:coding-exact-patch-body",
                label="Exact patch body artifact",
                status="missing",
                safe_summary=(
                    "The current proposal lane exposes safe refs and summaries but "
                    "does not store an exact patch body or raw diff."
                ),
                evidence_refs=evidence_refs,
                blocked_authority_refs=["blocked-state:coding-no-exact-patch-body"],
            ),
            CodingPatchApplyPrerequisiteReadModel(
                prerequisite_ref="prereq-ref:coding-hunk-selection-contract",
                label="Selected file or hunk scope",
                status="missing",
                safe_summary=(
                    "The cockpit has no backend contract for selected file or hunk "
                    "application scope."
                ),
                evidence_refs=evidence_refs,
                blocked_authority_refs=["blocked-state:coding-no-hunk-apply-contract"],
            ),
            CodingPatchApplyPrerequisiteReadModel(
                prerequisite_ref="prereq-ref:coding-local-approval-binding",
                label="Exact approval binding",
                status="blocked",
                safe_summary=(
                    "Approval mode labels are visible, but no Coding apply route "
                    "validates LocalApprovalAuthority for a selected proposal."
                ),
                evidence_refs=evidence_refs,
                blocked_authority_refs=["blocked-state:coding-no-approval-binding"],
            ),
            CodingPatchApplyPrerequisiteReadModel(
                prerequisite_ref="prereq-ref:coding-checkpoint-and-rollback",
                label="Checkpoint and rollback receipts",
                status="blocked",
                safe_summary=(
                    "Coding has no checkpoint, apply receipt, rollback receipt, or "
                    "proof binding for patch application."
                ),
                evidence_refs=evidence_refs,
                blocked_authority_refs=[
                    "blocked-state:coding-no-checkpoint-contract",
                    "blocked-state:coding-no-rollback-contract",
                ],
            ),
            CodingPatchApplyPrerequisiteReadModel(
                prerequisite_ref="prereq-ref:coding-sensitive-diff-guard",
                label="Sensitive diff blocking",
                status="missing",
                safe_summary=(
                    "Coding apply needs a verifier-backed guard that blocks sensitive "
                    "values, generated output, deletes, and sensitive config unless "
                    "separately approved."
                ),
                evidence_refs=evidence_refs,
                blocked_authority_refs=[
                    "blocked-state:coding-no-sensitive-diff-guard"
                ],
            ),
        ],
        expected_receipt_refs=[
            "receipt-ref:coding-patch-apply-required",
            "receipt-ref:coding-rollback-required",
        ],
        rollback_refs=["rollback-ref:coding-patch-apply-required"],
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path:coding-approved-patch-apply-contract",
            "promotion-path:coding-approved-patch-apply-route",
            "promotion-path:coding-approved-patch-apply-cli",
            "promotion-path:coding-approved-patch-apply-verifier",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
            "redaction-ref:diff-body-omitted",
        ],
        next_safe_action=(
            "Run the unblock prompt for exact approved patch apply only after the "
            "patch body, approval, checkpoint, rollback, redaction, proof, and CLI "
            "contracts are all in scope."
        ),
    )


def build_coding_test_command_readiness() -> CodingTestCommandReadinessReadModel:
    evidence_refs = ["evidence-ref:coding-test-command-readiness"]
    proof_refs = ["proof-ref:coding-test-command-readiness"]
    blocked_refs = [
        "blocked-state:coding-no-arbitrary-shell",
        "blocked-state:coding-no-install-command",
        "blocked-state:coding-no-network-command",
        "blocked-state:coding-no-destructive-command",
        "blocked-state:coding-no-background-process",
    ]
    suggested_commands = [
        CodingSuggestedTestCommandReadModel(
            command_ref="command-ref:coding-focused-pytest",
            label="Focused backend pytest",
            command_kind="focused_pytest",
            status="approval_required_runtime_lane",
            safe_command_summary=(
                "Maps to the RuntimeGateway focused pytest intent with fixed argv, "
                "exact approval, idempotency, timeout, and redacted receipt refs."
            ),
            allowlist_ref="runtime-command-shape-ref:focused-pytest",
            runtime_lane_ref="lane-ref:runtime-gateway:focused-pytest-action-inbox",
            runtime_command_intent="focused_pytest",
            expected_receipt_ref="receipt-plan:runtime-action-inbox:focused-pytest",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=blocked_refs,
        ),
        CodingSuggestedTestCommandReadModel(
            command_ref="command-ref:coding-repo-verifier",
            label="Repo documentation verifier",
            command_kind="repo_verifier",
            status="approval_required_runtime_lane",
            safe_command_summary=(
                "Maps to the RuntimeGateway repo verifier intent with fixed verifier "
                "argv, exact approval, idempotency, and redacted receipt refs."
            ),
            allowlist_ref="runtime-command-shape-ref:repo-verifier",
            runtime_lane_ref="lane-ref:runtime-gateway:repo-verifier-action-inbox",
            runtime_command_intent="repo_verifier",
            expected_receipt_ref="receipt-plan:runtime-action-inbox:repo-verifier",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=blocked_refs,
        ),
        CodingSuggestedTestCommandReadModel(
            command_ref="command-ref:coding-frontend-check",
            label="Frontend check",
            command_kind="frontend_check",
            status="approval_required_runtime_lane",
            safe_command_summary=(
                "Maps to the RuntimeGateway frontend check intent with fixed command "
                "wrapper, exact approval, idempotency, and redacted receipt refs."
            ),
            allowlist_ref="runtime-command-shape-ref:frontend-check",
            runtime_lane_ref="lane-ref:runtime-gateway:frontend-check-action-inbox",
            runtime_command_intent="frontend_check",
            expected_receipt_ref="receipt-plan:runtime-action-inbox:frontend-check",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=blocked_refs,
        ),
        CodingSuggestedTestCommandReadModel(
            command_ref="command-ref:coding-repo-doctor",
            label="Repo doctor",
            command_kind="repo_doctor",
            status="approval_required_runtime_lane",
            safe_command_summary=(
                "Maps to the RuntimeGateway repo doctor intent with fixed command "
                "wrapper, exact approval, idempotency, and redacted receipt refs."
            ),
            allowlist_ref="runtime-command-shape-ref:repo-doctor",
            runtime_lane_ref="lane-ref:runtime-gateway:repo-doctor-action-inbox",
            runtime_command_intent="repo_doctor",
            expected_receipt_ref="receipt-plan:runtime-action-inbox:repo-doctor",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=blocked_refs,
        ),
    ]
    return CodingTestCommandReadinessReadModel(
        title="Allowlisted test command readiness",
        full_strength_goal=(
            "Run focused allowlisted validation commands through RuntimeGateway "
            "with exact approval, fixed argv, redacted output summaries, exit "
            "codes, receipts, and Proof links."
        ),
        repo_safe_current_state=(
            "The Coding Cockpit exposes the existing approval-required RuntimeGateway "
            "validation lanes for inspection. This route still runs no command and "
            "stores no raw command or output."
        ),
        safe_summary=(
            "Exact validation commands are available only through RuntimeGateway "
            "Action Inbox approval envelopes; arbitrary shell, installs, network "
            "commands, destructive commands, and background processes remain blocked."
        ),
        allowlist_refs=[item.allowlist_ref for item in suggested_commands],
        suggested_commands=suggested_commands,
        expected_receipt_refs=[
            item.expected_receipt_ref for item in suggested_commands
        ],
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        unblock_prompt_refs=[],
        promotion_path_refs=[
            "promotion-path:coding-validation-runtime-lane-action-inbox",
            "promotion-path:coding-validation-runtime-lane-receipts",
            "promotion-path:coding-validation-runtime-lane-proof-detail",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-command-omitted",
            "redaction-ref:raw-output-omitted",
            "redaction-ref:bounded-summary-required",
        ],
        next_safe_action=(
            "Use the RuntimeGateway Action Inbox execution path for exact approved "
            "validation commands; keep Coding Cockpit as an inspection surface."
        ),
    )


def build_coding_git_review() -> CodingGitReviewReadModel:
    evidence_refs = ["evidence-ref:coding-git-review"]
    proof_refs = ["proof-ref:coding-git-review"]
    blocked_refs = [
        "blocked-state:coding-no-shell-subprocess",
        "blocked-state:coding-no-git-status-reader",
        "blocked-state:coding-no-git-diff-reader",
        "blocked-state:coding-no-git-mutation",
        "blocked-state:coding-no-stage",
        "blocked-state:coding-no-commit",
        "blocked-state:coding-no-push",
        "blocked-state:coding-no-pr-open",
        "blocked-state:coding-no-git-receipt",
    ]
    review_items = [
        CodingGitReviewItemReadModel(
            item_ref="git-status-ref:coding-working-tree-posture",
            label="Working tree status",
            item_kind="status",
            status="blocked",
            safe_summary=(
                "Would show branch and staged or unstaged posture after a "
                "read-only Git status reader is approved."
            ),
            expected_receipt_ref="git-receipt-ref:coding-status-required",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-git-status-reader",
            ],
        ),
        CodingGitReviewItemReadModel(
            item_ref="git-diff-ref:coding-safe-diff-posture",
            label="Diff posture",
            item_kind="diff",
            status="blocked",
            safe_summary=(
                "Would summarize Git diff refs after raw diff redaction and "
                "read-only Git diff contracts exist."
            ),
            expected_receipt_ref="git-receipt-ref:coding-diff-required",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-git-diff-reader",
            ],
        ),
        CodingGitReviewItemReadModel(
            item_ref="git-changed-files-ref:coding-safe-file-posture",
            label="Changed file refs",
            item_kind="changed_files",
            status="blocked",
            safe_summary=(
                "Would show changed file refs without raw local paths after a "
                "read-only Git status contract exists."
            ),
            expected_receipt_ref="git-receipt-ref:coding-changed-files-required",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-git-status-reader",
            ],
        ),
        CodingGitReviewItemReadModel(
            item_ref="git-commit-proposal-ref:coding-message-required",
            label="Commit proposal",
            item_kind="commit_proposal",
            status="proposal_ref",
            safe_summary=(
                "Commit proposal text remains absent until safe diff summaries, "
                "operator review, and receipt contracts exist."
            ),
            expected_receipt_ref="git-receipt-ref:coding-commit-proposal-required",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-git-receipt",
                "blocked-state:coding-no-commit",
            ],
        ),
        CodingGitReviewItemReadModel(
            item_ref="git-pr-description-ref:coding-pr-text-required",
            label="PR description proposal",
            item_kind="pr_description_proposal",
            status="proposal_ref",
            safe_summary=(
                "Pull-request description text remains absent until safe change "
                "summaries, proof refs, and operator review contracts exist."
            ),
            expected_receipt_ref="git-receipt-ref:coding-pr-description-required",
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-git-receipt",
                "blocked-state:coding-no-pr-open",
            ],
        ),
    ]
    return CodingGitReviewReadModel(
        title="Git review readiness",
        full_strength_goal=(
            "Review Git status, diffs, changed files, staged and unstaged posture, "
            "commit proposals, pull-request description proposals, and approved "
            "Git actions with receipts."
        ),
        repo_safe_current_state=(
            "Prompt 06 records Git review refs and proposal placeholders only. "
            "No Git command is run, no raw diff is stored, and no Git mutation "
            "route exists."
        ),
        safe_summary=(
            "Git review remains blocked until UAA has read-only Git status and "
            "diff contracts, redaction, receipts, proof binding, CLI parity, and "
            "separate approval for any stage, commit, push, or PR action."
        ),
        status_refs=["git-status-ref:coding-working-tree-posture"],
        changed_file_refs=["git-changed-files-ref:coding-safe-file-posture"],
        diff_refs=["git-diff-ref:coding-safe-diff-posture"],
        commit_proposal_refs=["git-commit-proposal-ref:coding-message-required"],
        pr_description_proposal_refs=[
            "git-pr-description-ref:coding-pr-text-required"
        ],
        expected_receipt_refs=[
            item.expected_receipt_ref for item in review_items
        ],
        review_items=review_items,
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path:coding-git-read-contract",
            "promotion-path:coding-git-review-route",
            "promotion-path:coding-git-review-cli",
            "promotion-path:coding-approved-git-mutation",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-git-output-omitted",
            "redaction-ref:raw-diff-omitted",
            "redaction-ref:raw-paths-omitted",
        ],
        next_safe_action=(
            "Run the unblock prompt only after read-only Git status, diff "
            "redaction, receipt, proof, and CLI contracts are in scope."
        ),
    )


def build_coding_live_preview() -> CodingLivePreviewReadModel:
    evidence_refs = ["evidence-ref:coding-live-preview"]
    proof_refs = ["proof-ref:coding-live-preview"]
    blocked_refs = [
        "blocked-state:coding-no-shell-subprocess",
        "blocked-state:coding-no-dev-server-status-detection",
        "blocked-state:coding-no-dev-server-control",
        "blocked-state:coding-no-preview-url-persistence",
        "blocked-state:coding-no-screenshot-capture",
        "blocked-state:coding-no-console-capture",
        "blocked-state:coding-no-visual-regression",
        "blocked-state:coding-no-browser-preview",
        "blocked-state:coding-no-browser-automation",
    ]
    preview_items = [
        CodingLivePreviewItemReadModel(
            item_ref="preview-status-ref:coding-dev-server-posture",
            label="Dev server status",
            item_kind="dev_server_status",
            status="blocked",
            safe_summary=(
                "Would show local dev server posture after a read-only status "
                "manifest contract exists; no process is started or inspected now."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-shell-subprocess",
                "blocked-state:coding-no-dev-server-status-detection",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="preview-url-ref:coding-local-preview-required",
            label="Preview URL",
            item_kind="preview_url",
            status="proposal_ref",
            safe_summary=(
                "Would link an operator-supplied or manifest-owned preview URL ref "
                "after redaction and persistence contracts exist."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-preview-url-persistence",
                "blocked-state:coding-no-browser-preview",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="screenshot-ref:coding-preview-required",
            label="Screenshot proof",
            item_kind="screenshot",
            status="blocked",
            safe_summary=(
                "Would attach an existing screenshot artifact ref after artifact "
                "ownership, redaction, and proof contracts exist."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-screenshot-capture",
                "blocked-state:coding-no-browser-automation",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="console-error-ref:coding-preview-required",
            label="Console errors",
            item_kind="console_errors",
            status="blocked",
            safe_summary=(
                "Would show bounded console-error summary refs after browser "
                "observe and redaction contracts are approved."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-console-capture",
                "blocked-state:coding-no-browser-preview",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="visual-proof-ref:coding-regression-required",
            label="Visual regression proof",
            item_kind="visual_regression",
            status="blocked",
            safe_summary=(
                "Would compare screenshot refs against visual baselines after "
                "artifact capture and verifier contracts exist."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-visual-regression",
                "blocked-state:coding-no-screenshot-capture",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="route-checklist-ref:coding-preview-required",
            label="Route checklist",
            item_kind="route_checklist",
            status="planned",
            safe_summary=(
                "Would track operator-selected route refs for visual QA without "
                "navigating a browser until exact authority exists."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-browser-automation",
                "blocked-state:coding-no-browser-preview",
            ],
        ),
        CodingLivePreviewItemReadModel(
            item_ref="viewport-ref:coding-preview-required",
            label="Viewport matrix",
            item_kind="viewport",
            status="planned",
            safe_summary=(
                "Would track desktop and mobile viewport refs after visual proof "
                "contracts exist."
            ),
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-browser-automation",
                "blocked-state:coding-no-visual-regression",
            ],
        ),
    ]
    return CodingLivePreviewReadModel(
        title="Live preview readiness",
        full_strength_goal=(
            "Show local dev server status, browser preview, console errors, "
            "screenshots, visual regression proof, route checklists, and mobile "
            "and desktop preview evidence."
        ),
        repo_safe_current_state=(
            "Prompt 07 records live preview refs only. No dev server process is "
            "started or inspected, no URL is persisted, no browser is opened, no "
            "screenshot is captured, and no console output is read."
        ),
        safe_summary=(
            "Live preview remains blocked until UAA has dev-server status, URL "
            "redaction, browser observe, screenshot artifact, visual proof, "
            "receipt, proof, and CLI contracts."
        ),
        dev_server_status_refs=["preview-status-ref:coding-dev-server-posture"],
        preview_url_refs=["preview-url-ref:coding-local-preview-required"],
        screenshot_refs=["screenshot-ref:coding-preview-required"],
        visual_proof_refs=["visual-proof-ref:coding-regression-required"],
        route_checklist_refs=["route-checklist-ref:coding-preview-required"],
        viewport_refs=["viewport-ref:coding-preview-required"],
        console_error_refs=["console-error-ref:coding-preview-required"],
        preview_items=preview_items,
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path:coding-dev-server-status-contract",
            "promotion-path:coding-preview-url-redaction",
            "promotion-path:coding-browser-observe-contract",
            "promotion-path:coding-screenshot-artifact-contract",
            "promotion-path:coding-visual-proof-contract",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-url-omitted",
            "redaction-ref:raw-console-output-omitted",
            "redaction-ref:screenshot-artifact-omitted",
        ],
        next_safe_action=(
            "Run the unblock prompt only after dev-server status, URL redaction, "
            "browser observe, screenshot artifact, visual proof, receipt, proof, "
            "and CLI contracts are in scope."
        ),
    )


def build_coding_multi_agent_review() -> CodingMultiAgentReviewReadModel:
    evidence_refs = ["evidence-ref:coding-multi-agent-review"]
    proof_refs = ["proof-ref:coding-multi-agent-review"]
    blocked_refs = list(
        dict.fromkeys(
            [
                *CODING_COCKPIT_REQUIRED_BLOCKED_REFS,
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-provider-sdk-call",
                "blocked-state:coding-no-local-agent-execution",
                "blocked-state:coding-no-multi-agent-execution",
                "blocked-state:coding-no-background-dispatch",
                "blocked-state:coding-no-background-autonomy",
                "blocked-state:coding-no-context-injection",
                "blocked-state:coding-no-raw-prompt-persistence",
                "blocked-state:coding-no-raw-response-persistence",
                "blocked-state:coding-no-provider-payload-persistence",
            ]
        )
    )
    agent_slots = [
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-codex-implementer",
            label="Codex implementer",
            slot_kind="implementer",
            status="proposal_ref",
            safe_summary=(
                "Would hold a reviewed Codex implementation plan artifact ref; "
                "no Codex or provider call is dispatched by UAA."
            ),
            output_artifact_refs=["agent-artifact:coding-codex-plan-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-local-agent-execution",
                "blocked-state:coding-no-background-dispatch",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-claude-reviewer",
            label="Claude reviewer",
            slot_kind="reviewer",
            status="proposal_ref",
            safe_summary=(
                "Would hold a reviewed Claude second-opinion artifact ref after "
                "provider authority, redaction, and receipts exist."
            ),
            output_artifact_refs=["agent-artifact:coding-claude-review-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-provider-sdk-call",
                "blocked-state:coding-no-background-dispatch",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-local-verifier",
            label="Local verifier",
            slot_kind="local_verifier",
            status="blocked",
            safe_summary=(
                "Would hold local verifier result refs after allowlisted command "
                "and local-agent execution have implemented AuthorityLease scope, "
                "exact approval, receipts, and safe-disable posture."
            ),
            output_artifact_refs=["agent-artifact:coding-local-verifier-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-local-agent-execution",
                "blocked-state:coding-no-shell-subprocess",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-security-reviewer",
            label="Security reviewer",
            slot_kind="security_reviewer",
            status="proposal_ref",
            safe_summary=(
                "Would hold a security review artifact ref after the review "
                "contract defines redaction, receipts, and proof bindings."
            ),
            output_artifact_refs=["agent-artifact:coding-security-review-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-background-dispatch",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-ux-reviewer",
            label="UX reviewer",
            slot_kind="ux_reviewer",
            status="proposal_ref",
            safe_summary=(
                "Would hold a UX review artifact ref after the visual and agent "
                "review contracts exist."
            ),
            output_artifact_refs=["agent-artifact:coding-ux-review-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-provider-model-call",
                "blocked-state:coding-no-browser-automation",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-test-fixer",
            label="Test fixer",
            slot_kind="test_fixer",
            status="blocked",
            safe_summary=(
                "Would hold a test-fix proposal artifact ref after allowlisted "
                "test receipt and exact patch proposal contracts exist."
            ),
            output_artifact_refs=["agent-artifact:coding-test-fixer-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-command-execution",
                "blocked-state:coding-no-local-agent-execution",
            ],
        ),
        CodingAgentReviewSlotReadModel(
            agent_slot_ref="agent-slot:coding-merge-captain",
            label="Merge captain",
            slot_kind="merge_captain",
            status="blocked",
            safe_summary=(
                "Would hold merge readiness refs after Git receipts, PR status, "
                "and explicit merge approval contracts exist."
            ),
            output_artifact_refs=["agent-artifact:coding-merge-captain-required"],
            proof_refs=proof_refs,
            evidence_refs=evidence_refs,
            blocked_authority_refs=[
                "blocked-state:coding-no-git-mutation",
                "blocked-state:coding-no-pr-open",
            ],
        ),
    ]
    return CodingMultiAgentReviewReadModel(
        title="Multi-agent review readiness",
        full_strength_goal=(
            "Coordinate Codex implementer, Claude reviewer, local verifier, "
            "security reviewer, UX reviewer, test fixer, and merge captain "
            "workflows with comparable plans, reviews, diffs, disagreements, "
            "receipts, and proof."
        ),
        repo_safe_current_state=(
            "Prompt 08 records multi-agent review slots and artifact refs only. "
            "No provider or model call, local agent execution, background "
            "dispatch, context injection, raw prompt or response persistence, "
            "or autonomous workflow execution occurs."
        ),
        safe_summary=(
            "Multi-agent review remains blocked until provider and local-agent "
            "authority, artifact, redaction, approval, receipt, proof, and CLI "
            "contracts exist."
        ),
        agent_slots=agent_slots,
        plan_artifact_refs=["agent-artifact:coding-plan-comparison-required"],
        review_artifact_refs=[
            "agent-artifact:coding-codex-plan-required",
            "agent-artifact:coding-claude-review-required",
            "agent-artifact:coding-local-verifier-required",
            "agent-artifact:coding-security-review-required",
            "agent-artifact:coding-ux-review-required",
            "agent-artifact:coding-test-fixer-required",
            "agent-artifact:coding-merge-captain-required",
        ],
        diff_comparison_refs=["agent-artifact:coding-diff-comparison-required"],
        disagreement_summary_refs=[
            "agent-artifact:coding-disagreement-summary-required"
        ],
        handoff_refs=["agent-handoff:coding-review-required"],
        pair_agent_relay=build_coding_pair_agent_relay_read_model(),
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path:coding-agent-artifact-contract",
            "promotion-path:coding-provider-review-authority",
            "promotion-path:coding-local-verifier-authority",
            "promotion-path:coding-agent-comparison-proof",
            "promotion-path:coding-approved-multi-agent-execution",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-prompts-omitted",
            "redaction-ref:raw-responses-omitted",
            "redaction-ref:provider-payloads-omitted",
        ],
        next_safe_action=(
            "Run the unblock prompt only after provider review, local-agent "
            "verification, artifact redaction, approval binding, receipts, "
            "proof, and CLI parity are in scope."
        ),
    )
