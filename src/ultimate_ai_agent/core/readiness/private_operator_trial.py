from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


PRIVATE_OPERATOR_TRIAL_CONTRACT_REF = (
    "contract-ref:private-operator-ui-functional-tuning:v1"
)

PrivateOperatorTrialSurface = Literal[
    "Local Boot",
    "Today",
    "Actions",
    "Memory",
    "Evidence",
    "Chat/Plans Handoff",
    "Blocked State Language",
    "CRM-Lite Follow-Ups",
]

PrivateOperatorTrialState = Literal[
    "pass",
    "partial",
    "blocked",
    "needs_operator_review",
]

PrivateOperatorTrialRunState = Literal[
    "not_started",
    "operator_review_ready",
    "in_review",
    "accepted_with_changes",
    "needs_revision",
    "blocked",
]

PrivateOperatorTrialReviewState = Literal[
    "pending_operator_review",
    "accepted",
    "revised",
    "blocked",
    "needs_follow_up",
]

PrivateOperatorTrialManualAnswerState = Literal[
    "unanswered_pending_manual_review",
]

PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES: list[PrivateOperatorTrialSurface] = [
    "Local Boot",
    "Today",
    "Actions",
    "Memory",
    "Evidence",
    "Chat/Plans Handoff",
    "Blocked State Language",
    "CRM-Lite Follow-Ups",
]

PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-public-beta",
    "blocked-state:no-public-distribution",
    "blocked-state:no-production-readiness-claim",
    "blocked-state:no-production-authority",
    "blocked-state:no-connector-write",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-account-sync",
    "blocked-state:no-crm-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-action-execution",
    "blocked-state:no-code-apply-execution",
    "blocked-state:openwebui-secondary-only",
]

_DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "action_execution_enabled",
    "code_apply_execution_enabled",
    "runtime_authority_added",
    "backend_route_added",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw screenshot",
    "raw_screenshot",
    "raw ocr",
    "raw_ocr",
    "raw file",
    "raw_file",
    "raw log",
    "raw_log",
    "browser state",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "token",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class PrivateOperatorTrialChecklistItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    surface: PrivateOperatorTrialSurface
    trial_state: PrivateOperatorTrialState
    safe_summary: str = Field(..., min_length=1, max_length=420)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    friction_refs: list[str] = Field(default_factory=list)
    ui_copy_task_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "PrivateOperatorTrialChecklistItem":
        _safe_ref(self.item_ref, "item_ref")
        for field_name in [
            "evidence_refs",
            "friction_refs",
            "ui_copy_task_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in ["surface", "trial_state", "safe_summary", "next_safe_action"]:
            _safe_text(str(getattr(self, field_name)), field_name)
        if not self.local_private_only:
            raise ValueError("private operator trial must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private operator trial must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private operator trial requires manual operator review")
        missing_blocked = set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private operator trial checklist item missing blocked refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private operator trial")
        return self


class PrivateOperatorTrialPacket(BaseModel):
    contract_ref: str = PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    milestone_ref: str = "milestone:uaa-p1-087.2a"
    status: str = "implemented_private_trial_packet_ui_surface_authority_blocked"
    trial_scope_ref: str = "trial-scope:private-operator-ui-functional-tuning"
    boot_command_ref: str = "launcher-command:uaa-trial-boot"
    checklist_items: list[PrivateOperatorTrialChecklistItem] = Field(
        default_factory=list, min_length=1
    )
    friction_finding_refs: list[str] = Field(default_factory=list, min_length=1)
    ui_copy_task_refs: list[str] = Field(default_factory=list, min_length=1)
    core_loop_gap_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = (
        "Use the private-trial packet to run local/private UI tuning for acceptance review, "
        "then keep UAA-P1-087.3 source-only until native boot cockpit scope is accepted."
    )
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_packet(self) -> "PrivateOperatorTrialPacket":
        if self.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
            raise ValueError("private operator trial contract ref drifted")
        for field_name in [
            "contract_ref",
            "milestone_ref",
            "trial_scope_ref",
            "boot_command_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "status",
            "next_safe_action",
        ]:
            _safe_text(getattr(self, field_name), field_name)
        for field_name in [
            "friction_finding_refs",
            "ui_copy_task_refs",
            "core_loop_gap_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        if {item.surface for item in self.checklist_items} != set(
            PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
        ):
            raise ValueError("private operator trial checklist missing required surfaces")
        missing_blocked = set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private operator trial packet missing blocked refs")
        if not self.local_private_only:
            raise ValueError("private operator trial must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private operator trial must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private operator trial requires manual operator review")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private operator trial")
        return self


class PrivateOperatorTrialSurfaceReview(BaseModel):
    review_ref: str = Field(..., min_length=1)
    surface: PrivateOperatorTrialSurface
    review_state: PrivateOperatorTrialReviewState
    reviewer_ref: str = Field(..., min_length=1)
    finding_refs: list[str] = Field(default_factory=list, min_length=1)
    friction_refs: list[str] = Field(default_factory=list)
    ui_copy_task_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    blocker_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_surface_review(self) -> "PrivateOperatorTrialSurfaceReview":
        for field_name in ["review_ref", "reviewer_ref"]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "finding_refs",
            "friction_refs",
            "ui_copy_task_refs",
            "evidence_refs",
            "blocker_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "surface",
            "review_state",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        if not self.local_private_only:
            raise ValueError("private trial surface review must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private trial surface review must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private trial surface review requires manual review")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private trial surface review")
        return self


class PrivateOperatorTrialAcceptanceLedger(BaseModel):
    ledger_ref: str = "ledger-ref:private-operator-trial-acceptance:v1"
    contract_ref: str = PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    milestone_ref: str = "milestone:uaa-p1-087.2b"
    status: str = "implemented_private_trial_acceptance_ledger_authority_blocked"
    source_packet_ref: str = "packet-ref:private-operator-trial:v1"
    trial_run_state: PrivateOperatorTrialRunState = "operator_review_ready"
    surface_reviews: list[PrivateOperatorTrialSurfaceReview] = Field(
        default_factory=list, min_length=1
    )
    manual_smoke_step_refs: list[str] = Field(default_factory=list, min_length=1)
    acceptance_question_refs: list[str] = Field(default_factory=list, min_length=1)
    tuning_decision_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS)
    )
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = (
        "Run local/private operator review against this ledger, record accepted or "
        "revised safe refs, then complete full UAA-P1-087.2 only after findings exist."
    )
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_acceptance_ledger(self) -> "PrivateOperatorTrialAcceptanceLedger":
        if self.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
            raise ValueError("private trial acceptance ledger contract ref drifted")
        for field_name in [
            "ledger_ref",
            "contract_ref",
            "milestone_ref",
            "source_packet_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in ["status", "trial_run_state", "next_safe_action"]:
            _safe_text(str(getattr(self, field_name)), field_name)
        for field_name in [
            "manual_smoke_step_refs",
            "acceptance_question_refs",
            "tuning_decision_refs",
            "blocked_state_refs",
            "evidence_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        if {review.surface for review in self.surface_reviews} != set(
            PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
        ):
            raise ValueError("private trial acceptance ledger missing required surfaces")
        missing_blocked = set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private trial acceptance ledger missing blocked refs")
        if not self.local_private_only:
            raise ValueError("private trial acceptance ledger must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private trial acceptance ledger must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private trial acceptance ledger requires manual review")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(
                    f"{flag} is denied by private trial acceptance ledger"
                )
        return self


class PrivateOperatorTrialManualReviewItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    surface: PrivateOperatorTrialSurface
    answer_state: PrivateOperatorTrialManualAnswerState = (
        "unanswered_pending_manual_review"
    )
    review_question_ref: str = Field(..., min_length=1)
    pending_answer_ref: str = Field(..., min_length=1)
    safe_question: str = Field(..., min_length=1, max_length=360)
    expected_evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    implementation_prerequisite_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manual_review_item(self) -> "PrivateOperatorTrialManualReviewItem":
        for field_name in ["item_ref", "review_question_ref", "pending_answer_ref"]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "expected_evidence_refs",
            "implementation_prerequisite_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "surface",
            "answer_state",
            "safe_question",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        if self.answer_state != "unanswered_pending_manual_review":
            raise ValueError("private trial manual review answers must stay pending")
        missing_blocked = set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private trial manual review item missing blocked refs")
        if not self.local_private_only:
            raise ValueError("private trial manual review item must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private trial manual review item must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private trial manual review item requires manual review")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private trial manual review")
        return self


class PrivateOperatorTrialManualReviewScaffold(BaseModel):
    scaffold_ref: str = "scaffold-ref:private-operator-trial-manual-review:v1"
    contract_ref: str = PRIVATE_OPERATOR_TRIAL_CONTRACT_REF
    milestone_ref: str = "milestone:uaa-p1-087.2c"
    status: str = "implemented_private_trial_manual_review_scaffold_authority_blocked"
    source_ledger_ref: str = "ledger-ref:private-operator-trial-acceptance:v1"
    review_state: str = "manual_review_deferred_pending_implementation"
    review_items: list[PrivateOperatorTrialManualReviewItem] = Field(
        default_factory=list, min_length=1
    )
    unanswered_question_refs: list[str] = Field(default_factory=list, min_length=1)
    missing_implementation_refs: list[str] = Field(default_factory=list, min_length=1)
    deferred_decision_refs: list[str] = Field(default_factory=list, min_length=1)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS)
    )
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    next_safe_action: str = (
        "Keep manual review unanswered until more Founder Loop implementation exists, "
        "then record accepted or revised safe refs in a later full UAA-P1-087.2 trial."
    )
    local_private_only: bool = True
    safe_refs_only: bool = True
    manual_operator_review_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False
    runtime_authority_added: bool = False
    backend_route_added: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manual_review_scaffold(
        self,
    ) -> "PrivateOperatorTrialManualReviewScaffold":
        if self.contract_ref != PRIVATE_OPERATOR_TRIAL_CONTRACT_REF:
            raise ValueError("private trial manual review contract ref drifted")
        for field_name in [
            "scaffold_ref",
            "contract_ref",
            "milestone_ref",
            "source_ledger_ref",
        ]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in ["status", "review_state", "next_safe_action"]:
            _safe_text(str(getattr(self, field_name)), field_name)
        for field_name in [
            "unanswered_question_refs",
            "missing_implementation_refs",
            "deferred_decision_refs",
            "blocked_state_refs",
            "evidence_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        if {item.surface for item in self.review_items} != set(
            PRIVATE_OPERATOR_TRIAL_REQUIRED_SURFACES
        ):
            raise ValueError("private trial manual review scaffold missing surfaces")
        if {item.answer_state for item in self.review_items} != {
            "unanswered_pending_manual_review"
        }:
            raise ValueError("private trial manual review scaffold must stay unanswered")
        missing_blocked = set(PRIVATE_OPERATOR_TRIAL_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private trial manual review scaffold missing blocked refs")
        if not self.local_private_only:
            raise ValueError("private trial manual review scaffold must stay local/private")
        if not self.safe_refs_only:
            raise ValueError("private trial manual review scaffold must stay safe-ref-only")
        if not self.manual_operator_review_required:
            raise ValueError("private trial manual review scaffold requires manual review")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private trial manual review")
        return self


def build_private_operator_trial_packet() -> PrivateOperatorTrialPacket:
    return PrivateOperatorTrialPacket(
        checklist_items=_checklist_items(),
        friction_finding_refs=[
            "friction-ref:private-trial:blocked-state-language",
            "friction-ref:private-trial:chat-plan-handoff-proof",
            "friction-ref:private-trial:crm-lite-follow-up-gap",
        ],
        ui_copy_task_refs=[
            "ui-copy-task:private-trial:show-first-party-surface",
            "ui-copy-task:private-trial:name-secondary-openwebui",
            "ui-copy-task:private-trial:surface-next-safe-action",
        ],
        core_loop_gap_refs=[
            "gap-ref:private-trial:memory-decision-execution",
            "gap-ref:private-trial:action-decision-receipts",
            "gap-ref:private-trial:first-party-chat-receipts",
            "gap-ref:private-trial:crm-lite-local-follow-up-store",
        ],
        evidence_refs=[
            "evidence-ref:private-trial:launcher-boot-readiness",
            "evidence-ref:private-trial:control-center-render-smoke",
            "evidence-ref:private-trial:manual-smoke-checklist",
            "evidence-ref:private-trial:ui-copy-task-ledger",
        ],
    )


def build_private_operator_trial_acceptance_ledger() -> PrivateOperatorTrialAcceptanceLedger:
    return PrivateOperatorTrialAcceptanceLedger(
        surface_reviews=_surface_reviews(),
        manual_smoke_step_refs=[
            "manual-smoke-step:private-trial:boot-control-center",
            "manual-smoke-step:private-trial:review-today-spine",
            "manual-smoke-step:private-trial:review-actions-memory-evidence",
            "manual-smoke-step:private-trial:review-chat-plans-handoff",
            "manual-smoke-step:private-trial:record-blocked-follow-ups",
        ],
        acceptance_question_refs=[
            "acceptance-question:private-trial:first-screen-orientation",
            "acceptance-question:private-trial:today-scan-friction",
            "acceptance-question:private-trial:memory-confidence",
            "acceptance-question:private-trial:action-review-clarity",
            "acceptance-question:private-trial:evidence-history-readability",
            "acceptance-question:private-trial:blocked-state-next-action",
        ],
        tuning_decision_refs=[
            "tuning-decision:private-trial:pending-copy-trim",
            "tuning-decision:private-trial:pending-surface-order",
            "tuning-decision:private-trial:pending-memory-review-emphasis",
            "tuning-decision:private-trial:pending-crm-lite-positioning",
        ],
        evidence_refs=[
            "evidence-ref:private-trial:acceptance-ledger-v1",
            "evidence-ref:private-trial:manual-smoke-runbook",
            "evidence-ref:private-trial:pending-operator-findings",
        ],
    )


def build_private_operator_trial_manual_review_scaffold() -> PrivateOperatorTrialManualReviewScaffold:
    return PrivateOperatorTrialManualReviewScaffold(
        review_items=_manual_review_items(),
        unanswered_question_refs=[
            "review-question:private-trial:first-screen-orientation",
            "review-question:private-trial:today-workflow-readiness",
            "review-question:private-trial:actions-decision-clarity",
            "review-question:private-trial:memory-trust-and-control",
            "review-question:private-trial:evidence-history-confidence",
            "review-question:private-trial:chat-handoff-truth",
            "review-question:private-trial:blocked-copy-friction",
            "review-question:private-trial:crm-lite-follow-up-value",
        ],
        missing_implementation_refs=[
            "missing-implementation:founder-loop:release-surface-manifest",
            "missing-implementation:founder-loop:action-decision-receipts",
            "missing-implementation:founder-loop:memory-review-receipts",
            "missing-implementation:founder-loop:chat-receipt-handoff",
            "missing-implementation:founder-loop:evidence-productization",
        ],
        deferred_decision_refs=[
            "deferred-decision:private-trial:full-087-2-acceptance",
            "deferred-decision:private-trial:native-boot-cockpit",
            "deferred-decision:private-trial:beta-readiness-language",
        ],
        evidence_refs=[
            "evidence-ref:private-trial:manual-review-scaffold-v1",
            "evidence-ref:private-trial:unanswered-questions",
            "evidence-ref:private-trial:deferred-manual-review",
        ],
    )


def _checklist_items() -> list[PrivateOperatorTrialChecklistItem]:
    rows: list[tuple[PrivateOperatorTrialSurface, PrivateOperatorTrialState, str, str]] = [
        (
            "Local Boot",
            "pass",
            "The repo-local trial boot path opens Control Center first and keeps OpenWebUI secondary or blocked.",
            "Confirm launcher status, log refs, and secondary-shell blocked state before trial use.",
        ),
        (
            "Today",
            "partial",
            "Today exposes product spine, action, memory, evidence, intent, and readiness refs in one surface.",
            "Use trial findings to reduce scanning friction before broader product claims.",
        ),
        (
            "Actions",
            "partial",
            "Actions shows reviewable envelopes and memory-derived proposals while mutation remains disabled.",
            "Keep approve/edit/reject/defer as next backend-owned receipt work.",
        ),
        (
            "Memory",
            "partial",
            "Memory shows source, provenance, quality, decision, intake, and loop refs without writes.",
            "Focus the next memory work on real review decisions and durable receipts.",
        ),
        (
            "Evidence",
            "partial",
            "Evidence reads as history with proposed, approved, happened, changed, undoable, stale, and blocked refs.",
            "Keep evidence summaries compact enough for repeated operator review.",
        ),
        (
            "Chat/Plans Handoff",
            "blocked",
            "Chat and Plans handoff proof remains local-gated and review-only; output is not authority.",
            "Do not promote Chat until durable receipts and handoff refs are real.",
        ),
        (
            "Blocked State Language",
            "partial",
            "Blocked-state labels are visible, but trial copy still needs consistency review across core surfaces.",
            "Tune copy toward next safe action instead of compliance-only wording.",
        ),
        (
            "CRM-Lite Follow-Ups",
            "blocked",
            "CRM-lite follow-ups appear as safe memory/action refs only; local business state is not implemented.",
            "Plan local CRM-lite records after memory review and action receipts are durable.",
        ),
    ]
    items: list[PrivateOperatorTrialChecklistItem] = []
    for surface, state, summary, next_safe_action in rows:
        slug = _surface_slug(surface)
        items.append(
            PrivateOperatorTrialChecklistItem(
                item_ref=f"private-trial-check:{slug}",
                surface=surface,
                trial_state=state,
                safe_summary=summary,
                evidence_refs=[f"evidence-ref:private-trial:{slug}"],
                friction_refs=[f"friction-ref:private-trial:{slug}"],
                ui_copy_task_refs=[f"ui-copy-task:private-trial:{slug}"],
                next_safe_action=next_safe_action,
            )
        )
    return items


def _manual_review_items() -> list[PrivateOperatorTrialManualReviewItem]:
    rows: list[tuple[PrivateOperatorTrialSurface, str, str]] = [
        (
            "Local Boot",
            "Does the boot path make it obvious which surface is first-party and what is blocked?",
            "Wait for manual operator review after the local boot flow is used in context.",
        ),
        (
            "Today",
            "Does Today make the next useful business step visible without scanning too much?",
            "Wait for more Founder Loop implementation before scoring Today readiness.",
        ),
        (
            "Actions",
            "Can the operator understand approve, edit, reject, defer, receipt, and rollback posture?",
            "Implement backend decision receipts before manual acceptance.",
        ),
        (
            "Memory",
            "Does Memory feel trustworthy, correctable, and useful across business follow-ups?",
            "Implement durable review decisions before manual acceptance.",
        ),
        (
            "Evidence",
            "Does Evidence read like what was proposed, approved, happened, changed, and undoable?",
            "Productize Evidence Timeline receipts before manual acceptance.",
        ),
        (
            "Chat/Plans Handoff",
            "Does Chat show model, runtime, auth, tool-denial, and handoff truth clearly?",
            "Implement durable chat receipt and handoff refs before manual acceptance.",
        ),
        (
            "Blocked State Language",
            "Does blocked copy explain the next safe action without feeling like paperwork?",
            "Review copy after more surfaces have real backend state.",
        ),
        (
            "CRM-Lite Follow-Ups",
            "Do follow-up refs feel like useful business flow rather than generic memory notes?",
            "Implement local follow-up records after memory and action receipts exist.",
        ),
    ]
    items: list[PrivateOperatorTrialManualReviewItem] = []
    for surface, question, next_safe_action in rows:
        slug = _surface_slug(surface)
        items.append(
            PrivateOperatorTrialManualReviewItem(
                item_ref=f"manual-review-item:private-trial:{slug}",
                surface=surface,
                review_question_ref=f"review-question:private-trial:{slug}",
                pending_answer_ref=f"pending-answer:private-trial:{slug}",
                safe_question=question,
                expected_evidence_refs=[
                    f"evidence-ref:private-trial:manual-review:{slug}"
                ],
                implementation_prerequisite_refs=[
                    f"implementation-prereq:private-trial:{slug}"
                ],
                next_safe_action=next_safe_action,
            )
        )
    return items


def _surface_reviews() -> list[PrivateOperatorTrialSurfaceReview]:
    rows: list[tuple[PrivateOperatorTrialSurface, str]] = [
        ("Local Boot", "Confirm first-party launch, secondary-shell posture, and safe log refs."),
        ("Today", "Review whether Today makes the next operator step obvious."),
        ("Actions", "Review envelope clarity while approve/edit/reject/defer remains blocked."),
        ("Memory", "Review provenance, quality, and decision refs before memory writes exist."),
        ("Evidence", "Review whether history reads as proposed, approved, happened, changed, undoable."),
        ("Chat/Plans Handoff", "Review handoff clarity while Chat output stays non-authoritative."),
        ("Blocked State Language", "Review blocked copy for next safe action and low friction."),
        ("CRM-Lite Follow-Ups", "Review follow-up positioning without claiming local CRM state."),
    ]
    reviews: list[PrivateOperatorTrialSurfaceReview] = []
    for surface, next_safe_action in rows:
        slug = _surface_slug(surface)
        reviews.append(
            PrivateOperatorTrialSurfaceReview(
                review_ref=f"surface-review:private-trial:{slug}",
                surface=surface,
                review_state="pending_operator_review",
                reviewer_ref="operator-ref:local-private-reviewer",
                finding_refs=[f"finding-ref:private-trial:pending:{slug}"],
                friction_refs=[f"friction-ref:private-trial:{slug}"],
                ui_copy_task_refs=[f"ui-copy-task:private-trial:{slug}"],
                evidence_refs=[f"evidence-ref:private-trial:{slug}"],
                blocker_refs=[f"blocker-ref:private-trial:{slug}"],
                next_safe_action=next_safe_action,
            )
        )
    return reviews


def _surface_slug(surface: str) -> str:
    return surface.lower().replace("/", "-").replace(" ", "-")


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe private-trial text")
