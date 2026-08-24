from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalSubjectType,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseStore,
    TrustMode,
    build_default_authority_leases,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


WORK_BOARD_CONTRACT_REF = "contract-ref:work-board-kanban-shell:v1"
WORK_BOARD_BOARD_REF = "work-board:founder-command-center-kanban"
WORK_BOARD_ROUTE_REF = "route-ref:control-center-work-board"
WORK_BOARD_BACKEND_ROUTE_REF = "GET /control-center/work-board"
WORK_BOARD_REORDER_ROUTE_REF = "POST /control-center/work-board/reorder"
WORK_BOARD_CARD_CREATE_ROUTE_REF = "POST /control-center/work-board/cards"
WORK_BOARD_TASK_CREATE_ROUTE_REF = "POST /control-center/work-board/tasks"
WORK_BOARD_FRONTEND_ROUTE_REF = "/work-board"
WORK_BOARD_CLI_REF = "scripts/dev/uaa_work_board.py inspect-board"
WORK_BOARD_CARD_CREATE_CLI_REF = "scripts/dev/uaa_work_board.py inspect-card-create-receipt"
WORK_BOARD_TASK_CREATE_CLI_REF = "scripts/dev/uaa_work_board.py inspect-task-create-receipt"
WORK_BOARD_STATE_DIR_ENV = "UAA_WORK_BOARD_STATE_DIR"
WORK_BOARD_STATE_FILE = "work_board_state.json"
WORK_BOARD_RECEIPTS_FILE = "work_board_receipts.jsonl"
WORK_BOARD_CARD_CREATE_RECEIPTS_FILE = "work_board_card_create_receipts.jsonl"
WORK_BOARD_TASK_CREATE_RECEIPTS_FILE = "work_board_task_create_receipts.jsonl"
WORK_BOARD_REORDER_REQUESTED_ACTION = "persist_work_board_reorder"
WORK_BOARD_CARD_CREATE_REQUESTED_ACTION = "persist_work_board_card_create"
WORK_BOARD_TASK_CREATE_REQUESTED_ACTION = "persist_work_board_task_create"
WORK_BOARD_REORDER_SAFE_DISABLE_REF = "safe-disable-ref:work-board:durable-reorder"
WORK_BOARD_REORDER_ROLLBACK_REF = "rollback-ref:work-board:restore-previous-order"
WORK_BOARD_REORDER_PROOF_REF = "proof-ref:work-board-durable-reorder"
WORK_BOARD_REORDER_EVIDENCE_REF = "evidence-ref:work-board-durable-reorder"
WORK_BOARD_CARD_CREATE_SAFE_DISABLE_REF = "safe-disable-ref:work-board:local-card-create"
WORK_BOARD_CARD_CREATE_ROLLBACK_REF = "rollback-ref:work-board:remove-local-created-card"
WORK_BOARD_CARD_CREATE_PROOF_REF = "proof-ref:work-board-local-card-create"
WORK_BOARD_CARD_CREATE_EVIDENCE_REF = "evidence-ref:work-board-local-card-create"
WORK_BOARD_TASK_CREATE_SAFE_DISABLE_REF = "safe-disable-ref:work-board:local-task-create"
WORK_BOARD_TASK_CREATE_ROLLBACK_REF = "rollback-ref:work-board:remove-local-task-record"
WORK_BOARD_TASK_CREATE_PROOF_REF = "proof-ref:work-board-local-task-create"
WORK_BOARD_TASK_CREATE_EVIDENCE_REF = "evidence-ref:work-board-local-task-create"
WORK_BOARD_SOCIAL_CONTENT_PROJECTION_REF = "work-board-saved-projection:social-content"
WORK_BOARD_SOCIAL_CONTENT_PROJECTION_CONTRACT_REF = (
    "contract-ref:work-board-social-content-saved-projection:v1"
)
WORK_BOARD_SOCIAL_CONTENT_CARD_REF = "work-board-card:social-read-only-foundation"
WORK_BOARD_SOCIAL_CONTENT_FILTER_TAG = "social-content"
WORK_BOARD_AUTHORITY_DOMAIN_REF = "authority-domain-ref:workspace"
WORK_BOARD_AUTHORITY_CAPABILITY_REF = "authority-capability-ref:write"
WORK_BOARD_REORDER_AUTHORITY_ACTION_REF = "authority-action-ref:work-board-reorder"
WORK_BOARD_CARD_CREATE_AUTHORITY_ACTION_REF = (
    "authority-action-ref:work-board-card-create"
)
WORK_BOARD_TASK_CREATE_AUTHORITY_ACTION_REF = (
    "authority-action-ref:work-board-task-create"
)
WORK_BOARD_BLOCKED_CARD_ARCHIVE_ASSIGNMENT_REF = (
    "blocked-state:work-board-no-card-archive-assignment"
)
WORK_BOARD_REQUIRED_BLOCKED_REFS = [
    WORK_BOARD_BLOCKED_CARD_ARCHIVE_ASSIGNMENT_REF,
    "blocked-state:work-board-no-issue-tracker-write",
    "blocked-state:work-board-no-connector-write",
    "blocked-state:work-board-no-provider-model-call",
    "blocked-state:work-board-no-shell-subprocess",
    "blocked-state:work-board-no-browser-automation",
    "blocked-state:work-board-no-background-autonomy",
    "blocked-state:work-board-no-production-authority",
]


BoardStatus = Literal["backend_owned_read_model"]
ColumnStatus = Literal["planned", "in_progress", "review", "blocked", "done"]
CardPriority = Literal["critical", "high", "medium", "low"]
CardAuthorityState = Literal["enabled_read_only", "proposal_only", "blocked"]
SavedProjectionStatus = Literal["backend_owned_read_only"]


def _hash_ref(prefix: str, value: object) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def work_board_state_dir() -> Path:
    value = os.environ.get(WORK_BOARD_STATE_DIR_ENV, "").strip()
    if value:
        return Path(value).expanduser()
    return Path(".uaa") / "work_board"


def _work_board_actor_context(approval_ref: str | None = None) -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="local_operator",
        authority_source=AuthoritySource.explicit_user_request,
        approval_ref=approval_ref,
    )


class WorkBoardBlockedLaneReadModel(BaseModel):
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "WorkBoardBlockedLaneReadModel":
        for ref in [
            self.lane_ref,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
        ]:
            validate_task_ref(ref, "work_board_blocked_lane_ref")
        for value in [self.label, self.safe_summary]:
            validate_safe_task_text(value, "work_board_blocked_lane_text")
        if not self.blocked_authority_refs:
            raise ValueError("blocked work board lane requires blocker refs")
        return self


class WorkBoardReorderColumnRequest(BaseModel):
    column_ref: str = Field(..., min_length=1)
    card_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_column_request(self) -> "WorkBoardReorderColumnRequest":
        validate_task_ref(self.column_ref, "work_board_reorder_column_ref")
        for card_ref in self.card_refs:
            validate_task_ref(card_ref, "work_board_reorder_card_ref")
        return self


class WorkBoardReorderRequest(BaseModel):
    board_ref: str = WORK_BOARD_BOARD_REF
    decision: Literal["approve"] = "approve"
    approval_ref: str | None = None
    exact_scope_ref: str | None = None
    action_envelope_ref: str | None = None
    decision_reason_ref: str = Field(..., min_length=1)
    columns: list[WorkBoardReorderColumnRequest] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_reorder_request(self) -> "WorkBoardReorderRequest":
        validate_task_ref(self.board_ref, "work_board_reorder_board_ref")
        validate_task_ref(
            self.decision_reason_ref,
            "work_board_reorder_decision_reason_ref",
        )
        for value, field_name in [
            (self.approval_ref, "work_board_reorder_approval_ref"),
            (self.exact_scope_ref, "work_board_reorder_exact_scope_ref"),
            (self.action_envelope_ref, "work_board_reorder_action_envelope_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for ref in self.metadata_refs:
            validate_task_ref(ref, "work_board_reorder_metadata_ref")
        if not self.columns:
            raise ValueError("work board reorder requires column ordering")
        return self


class WorkBoardCardCreateRequest(BaseModel):
    board_ref: str = WORK_BOARD_BOARD_REF
    decision: Literal["approve"] = "approve"
    approval_ref: str | None = None
    exact_scope_ref: str | None = None
    action_envelope_ref: str | None = None
    decision_reason_ref: str = Field(..., min_length=1)
    column_ref: str = "work-board-column:triage"
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=360)
    priority: CardPriority = "medium"
    tags: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_card_create_request(self) -> "WorkBoardCardCreateRequest":
        for value, field_name in [
            (self.board_ref, "work_board_card_create_board_ref"),
            (self.decision_reason_ref, "work_board_card_create_decision_reason_ref"),
            (self.column_ref, "work_board_card_create_column_ref"),
            (self.approval_ref, "work_board_card_create_approval_ref"),
            (self.exact_scope_ref, "work_board_card_create_exact_scope_ref"),
            (self.action_envelope_ref, "work_board_card_create_action_envelope_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for value in [self.title, self.safe_summary, self.priority, *self.tags]:
            validate_safe_task_text(value, "work_board_card_create_text")
        for ref in self.metadata_refs:
            validate_task_ref(ref, "work_board_card_create_metadata_ref")
        if self.board_ref != WORK_BOARD_BOARD_REF:
            raise ValueError("work board card create board ref mismatch")
        return self


class WorkBoardTaskCreateRequest(BaseModel):
    board_ref: str = WORK_BOARD_BOARD_REF
    decision: Literal["approve"] = "approve"
    approval_ref: str | None = None
    exact_scope_ref: str | None = None
    action_envelope_ref: str | None = None
    decision_reason_ref: str = Field(..., min_length=1)
    card_ref: str = Field(..., min_length=1)
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_task_create_request(self) -> "WorkBoardTaskCreateRequest":
        for value, field_name in [
            (self.board_ref, "work_board_task_create_board_ref"),
            (self.decision_reason_ref, "work_board_task_create_decision_reason_ref"),
            (self.card_ref, "work_board_task_create_card_ref"),
            (self.approval_ref, "work_board_task_create_approval_ref"),
            (self.exact_scope_ref, "work_board_task_create_exact_scope_ref"),
            (self.action_envelope_ref, "work_board_task_create_action_envelope_ref"),
        ]:
            if value is not None:
                validate_task_ref(value, field_name)
        for ref in self.metadata_refs:
            validate_task_ref(ref, "work_board_task_create_metadata_ref")
        if self.board_ref != WORK_BOARD_BOARD_REF:
            raise ValueError("work board task create board ref mismatch")
        return self


class WorkBoardReorderReceipt(BaseModel):
    schema_version: Literal["uaa-work-board-reorder-receipt.v1"] = (
        "uaa-work-board-reorder-receipt.v1"
    )
    contract_ref: str = "contract-ref:work-board-durable-reorder:v1"
    board_ref: str
    receipt_ref: str
    status: Literal["applied", "replayed"]
    approval_ref: str
    approval_decision_ref: str
    approval_validation_ref: str
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain_ref: str = WORK_BOARD_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = WORK_BOARD_AUTHORITY_CAPABILITY_REF
    exact_scope_ref: str
    action_envelope_ref: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    previous_order_ref: str
    new_order_ref: str
    safe_disable_ref: str = WORK_BOARD_REORDER_SAFE_DISABLE_REF
    rollback_ref: str = WORK_BOARD_REORDER_ROLLBACK_REF
    proof_ref: str = WORK_BOARD_REORDER_PROOF_REF
    evidence_ref: str = WORK_BOARD_REORDER_EVIDENCE_REF
    route_ref: str = WORK_BOARD_REORDER_ROUTE_REF
    applied_at_ref: str
    safe_summary: str
    replayed: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    issue_tracker_write_performed: bool = False
    connector_write_performed: bool = False
    provider_model_call_performed: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_automation_performed: bool = False
    background_autonomy_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "WorkBoardReorderReceipt":
        for ref in [
            self.contract_ref,
            self.board_ref,
            self.receipt_ref,
            self.approval_ref,
            self.approval_decision_ref,
            self.approval_validation_ref,
            self.authority_domain_ref,
            self.authority_capability_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.previous_order_ref,
            self.new_order_ref,
            self.safe_disable_ref,
            self.rollback_ref,
            self.proof_ref,
            self.evidence_ref,
            self.applied_at_ref,
        ]:
            validate_task_ref(ref, "work_board_reorder_receipt_ref")
        for ref in [self.authority_decision_ref, self.authority_lease_ref]:
            if ref is not None:
                validate_task_ref(ref, "work_board_reorder_authority_ref")
        if self.authority_decision_outcome is not None:
            validate_safe_task_text(
                self.authority_decision_outcome,
                "work_board_reorder_authority_decision_outcome",
            )
            if self.authority_decision_outcome not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }:
                raise ValueError("work board reorder authority decision unsupported")
        validate_safe_task_text(self.route_ref, "work_board_reorder_route_ref")
        validate_safe_task_text(self.safe_summary, "work_board_reorder_summary")
        forbidden_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "issue_tracker_write_performed": self.issue_tracker_write_performed,
            "connector_write_performed": self.connector_write_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "shell_subprocess_execution_performed": (
                self.shell_subprocess_execution_performed
            ),
            "browser_automation_performed": self.browser_automation_performed,
            "background_autonomy_performed": self.background_autonomy_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board reorder receipt enabled {enabled[0]}")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_reorder_receipt",
        )
        return self


class WorkBoardCardCreateReceipt(BaseModel):
    schema_version: Literal["uaa-work-board-card-create-receipt.v1"] = (
        "uaa-work-board-card-create-receipt.v1"
    )
    contract_ref: str = "contract-ref:work-board-local-card-create:v1"
    board_ref: str
    card_ref: str
    receipt_ref: str
    status: Literal["applied", "replayed"]
    approval_ref: str
    approval_decision_ref: str
    approval_validation_ref: str
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain_ref: str = WORK_BOARD_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = WORK_BOARD_AUTHORITY_CAPABILITY_REF
    exact_scope_ref: str
    action_envelope_ref: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    previous_order_ref: str
    new_order_ref: str
    safe_disable_ref: str = WORK_BOARD_CARD_CREATE_SAFE_DISABLE_REF
    rollback_ref: str = WORK_BOARD_CARD_CREATE_ROLLBACK_REF
    proof_ref: str = WORK_BOARD_CARD_CREATE_PROOF_REF
    evidence_ref: str = WORK_BOARD_CARD_CREATE_EVIDENCE_REF
    route_ref: str = WORK_BOARD_CARD_CREATE_ROUTE_REF
    applied_at_ref: str
    safe_summary: str
    replayed: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    issue_tracker_write_performed: bool = False
    connector_write_performed: bool = False
    provider_model_call_performed: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_automation_performed: bool = False
    background_autonomy_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_card_create_receipt(self) -> "WorkBoardCardCreateReceipt":
        for ref in [
            self.contract_ref,
            self.board_ref,
            self.card_ref,
            self.receipt_ref,
            self.approval_ref,
            self.approval_decision_ref,
            self.approval_validation_ref,
            self.authority_domain_ref,
            self.authority_capability_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.previous_order_ref,
            self.new_order_ref,
            self.safe_disable_ref,
            self.rollback_ref,
            self.proof_ref,
            self.evidence_ref,
            self.applied_at_ref,
        ]:
            validate_task_ref(ref, "work_board_card_create_receipt_ref")
        for ref in [self.authority_decision_ref, self.authority_lease_ref]:
            if ref is not None:
                validate_task_ref(ref, "work_board_card_create_authority_ref")
        if self.authority_decision_outcome is not None:
            validate_safe_task_text(
                self.authority_decision_outcome,
                "work_board_card_create_authority_decision_outcome",
            )
            if self.authority_decision_outcome not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }:
                raise ValueError("work board card create authority decision unsupported")
        validate_safe_task_text(self.route_ref, "work_board_card_create_route_ref")
        validate_safe_task_text(self.safe_summary, "work_board_card_create_summary")
        forbidden_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "issue_tracker_write_performed": self.issue_tracker_write_performed,
            "connector_write_performed": self.connector_write_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "shell_subprocess_execution_performed": (
                self.shell_subprocess_execution_performed
            ),
            "browser_automation_performed": self.browser_automation_performed,
            "background_autonomy_performed": self.background_autonomy_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board card create receipt enabled {enabled[0]}")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_card_create_receipt",
        )
        return self


class WorkBoardTaskCreateReceipt(BaseModel):
    schema_version: Literal["uaa-work-board-task-create-receipt.v1"] = (
        "uaa-work-board-task-create-receipt.v1"
    )
    contract_ref: str = "contract-ref:work-board-local-task-create:v1"
    board_ref: str
    card_ref: str
    local_task_ref: str
    receipt_ref: str
    status: Literal["applied", "replayed"]
    approval_ref: str
    approval_decision_ref: str
    approval_validation_ref: str
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain_ref: str = WORK_BOARD_AUTHORITY_DOMAIN_REF
    authority_capability_ref: str = WORK_BOARD_AUTHORITY_CAPABILITY_REF
    exact_scope_ref: str
    action_envelope_ref: str
    idempotency_ref: str
    payload_fingerprint_ref: str
    safe_disable_ref: str = WORK_BOARD_TASK_CREATE_SAFE_DISABLE_REF
    rollback_ref: str = WORK_BOARD_TASK_CREATE_ROLLBACK_REF
    proof_ref: str = WORK_BOARD_TASK_CREATE_PROOF_REF
    evidence_ref: str = WORK_BOARD_TASK_CREATE_EVIDENCE_REF
    route_ref: str = WORK_BOARD_TASK_CREATE_ROUTE_REF
    applied_at_ref: str
    safe_summary: str
    replayed: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    task_execution_performed: bool = False
    issue_tracker_write_performed: bool = False
    connector_write_performed: bool = False
    provider_model_call_performed: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_automation_performed: bool = False
    background_autonomy_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_task_create_receipt(self) -> "WorkBoardTaskCreateReceipt":
        for ref in [
            self.contract_ref,
            self.board_ref,
            self.card_ref,
            self.local_task_ref,
            self.receipt_ref,
            self.approval_ref,
            self.approval_decision_ref,
            self.approval_validation_ref,
            self.authority_domain_ref,
            self.authority_capability_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.idempotency_ref,
            self.payload_fingerprint_ref,
            self.safe_disable_ref,
            self.rollback_ref,
            self.proof_ref,
            self.evidence_ref,
            self.applied_at_ref,
        ]:
            validate_task_ref(ref, "work_board_task_create_receipt_ref")
        for ref in [self.authority_decision_ref, self.authority_lease_ref]:
            if ref is not None:
                validate_task_ref(ref, "work_board_task_create_authority_ref")
        if self.authority_decision_outcome is not None:
            validate_safe_task_text(
                self.authority_decision_outcome,
                "work_board_task_create_authority_decision_outcome",
            )
            if self.authority_decision_outcome not in {
                AuthorityDecisionOutcome.allow.value,
                AuthorityDecisionOutcome.ask.value,
            }:
                raise ValueError("work board task create authority decision unsupported")
        validate_safe_task_text(self.route_ref, "work_board_task_create_route_ref")
        validate_safe_task_text(self.safe_summary, "work_board_task_create_summary")
        forbidden_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "task_execution_performed": self.task_execution_performed,
            "issue_tracker_write_performed": self.issue_tracker_write_performed,
            "connector_write_performed": self.connector_write_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "shell_subprocess_execution_performed": (
                self.shell_subprocess_execution_performed
            ),
            "browser_automation_performed": self.browser_automation_performed,
            "background_autonomy_performed": self.background_autonomy_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board task create receipt enabled {enabled[0]}")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_task_create_receipt",
        )
        return self


class WorkBoardReorderApprovalPreview(BaseModel):
    approval_request: ApprovalRequest
    expected_approval_ref: str
    exact_scope_ref: str
    action_envelope_ref: str
    payload_fingerprint_ref: str
    previous_order_ref: str
    new_order_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_preview(self) -> "WorkBoardReorderApprovalPreview":
        for ref in [
            self.expected_approval_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.payload_fingerprint_ref,
            self.previous_order_ref,
            self.new_order_ref,
        ]:
            validate_task_ref(ref, "work_board_reorder_approval_preview_ref")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_reorder_approval_preview",
        )
        return self


class WorkBoardCardCreateApprovalPreview(BaseModel):
    approval_request: ApprovalRequest
    expected_approval_ref: str
    exact_scope_ref: str
    action_envelope_ref: str
    payload_fingerprint_ref: str
    previous_order_ref: str
    new_order_ref: str
    card_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_card_create_preview(self) -> "WorkBoardCardCreateApprovalPreview":
        for ref in [
            self.expected_approval_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.payload_fingerprint_ref,
            self.previous_order_ref,
            self.new_order_ref,
            self.card_ref,
        ]:
            validate_task_ref(ref, "work_board_card_create_approval_preview_ref")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_card_create_approval_preview",
        )
        return self


class WorkBoardTaskCreateApprovalPreview(BaseModel):
    approval_request: ApprovalRequest
    expected_approval_ref: str
    exact_scope_ref: str
    action_envelope_ref: str
    payload_fingerprint_ref: str
    card_ref: str
    local_task_ref: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_task_create_preview(self) -> "WorkBoardTaskCreateApprovalPreview":
        for ref in [
            self.expected_approval_ref,
            self.exact_scope_ref,
            self.action_envelope_ref,
            self.payload_fingerprint_ref,
            self.card_ref,
            self.local_task_ref,
        ]:
            validate_task_ref(ref, "work_board_task_create_approval_preview_ref")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "work_board_task_create_approval_preview",
        )
        return self


class WorkBoardLocalTaskReadModel(BaseModel):
    local_task_ref: str = Field(..., min_length=1)
    card_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=140)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    status: Literal["local_task_recorded"] = "local_task_recorded"
    receipt_ref: str = Field(..., min_length=1)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    raw_path_included: bool = False
    raw_content_included: bool = False
    task_execution_enabled: bool = False
    issue_tracker_write_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_local_task(self) -> "WorkBoardLocalTaskReadModel":
        for ref in [
            self.local_task_ref,
            self.card_ref,
            self.receipt_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocker_refs,
        ]:
            validate_task_ref(ref, "work_board_local_task_ref")
        for value in [
            self.title,
            self.safe_summary,
            self.status,
            *self.cli_inspection_refs,
        ]:
            validate_safe_task_text(value, "work_board_local_task_text")
        forbidden_flags = {
            "raw_path_included": self.raw_path_included,
            "raw_content_included": self.raw_content_included,
            "task_execution_enabled": self.task_execution_enabled,
            "issue_tracker_write_enabled": self.issue_tracker_write_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "browser_automation_enabled": self.browser_automation_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board local task enabled {enabled[0]}")
        return self


class WorkBoardCardReadModel(BaseModel):
    card_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=140)
    safe_summary: str = Field(..., min_length=1, max_length=520)
    column_ref: str = Field(..., min_length=1)
    priority: CardPriority
    authority_state: CardAuthorityState
    owner_ref: str = Field(..., min_length=1)
    progress_label: str = Field(..., min_length=1, max_length=80)
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    surface_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    raw_path_included: bool = False
    raw_content_included: bool = False
    mutation_enabled: bool = False
    drag_persistence_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_card(self) -> "WorkBoardCardReadModel":
        for ref in [
            self.card_ref,
            self.column_ref,
            self.owner_ref,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocker_refs,
            *self.surface_refs,
        ]:
            validate_task_ref(ref, "work_board_card_ref")
        for value in (
            [
                self.title,
                self.safe_summary,
                self.priority,
                self.authority_state,
                self.progress_label,
            ]
            + self.cli_inspection_refs
            + self.tags
        ):
            validate_safe_task_text(value, "work_board_card_text")
        if self.raw_path_included:
            raise ValueError("work board card cannot include raw paths")
        if self.raw_content_included:
            raise ValueError("work board card cannot include raw content")
        if self.mutation_enabled:
            raise ValueError("work board card cannot enable mutation")
        if self.drag_persistence_enabled:
            raise ValueError("work board card cannot enable drag persistence")
        if self.authority_state == "blocked" and not self.blocker_refs:
            raise ValueError("blocked work board card requires blocker refs")
        return self


class WorkBoardColumnReadModel(BaseModel):
    column_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=80)
    status: ColumnStatus
    safe_summary: str = Field(..., min_length=1, max_length=360)
    card_refs: list[str] = Field(default_factory=list)
    wip_limit: int = Field(..., ge=1, le=24)
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_column(self) -> "WorkBoardColumnReadModel":
        for ref in [self.column_ref, *self.card_refs, *self.blocked_authority_refs]:
            validate_task_ref(ref, "work_board_column_ref")
        for value in [self.label, self.status, self.safe_summary]:
            validate_safe_task_text(value, "work_board_column_text")
        return self


class WorkBoardSavedProjectionReadModel(BaseModel):
    projection_ref: str = Field(..., min_length=1)
    contract_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=80)
    safe_summary: str = Field(..., min_length=1, max_length=420)
    owner_ref: str = Field(..., min_length=1)
    status: SavedProjectionStatus = "backend_owned_read_only"
    filter_tags: list[str] = Field(default_factory=list, min_length=1)
    link_contract_refs: list[str] = Field(default_factory=list, min_length=1)
    proof_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    blocker_refs: list[str] = Field(default_factory=list)
    backend_owned: bool = True
    read_only: bool = True
    copies_task_lifecycle: bool = False
    publishing_enabled: bool = False
    connector_write_enabled: bool = False
    background_sync_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_projection(self) -> "WorkBoardSavedProjectionReadModel":
        for ref in [
            self.projection_ref,
            self.contract_ref,
            self.owner_ref,
            *self.link_contract_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocker_refs,
        ]:
            validate_task_ref(ref, "work_board_saved_projection_ref")
        for value in [
            self.label,
            self.safe_summary,
            self.status,
            *self.filter_tags,
        ]:
            validate_safe_task_text(value, "work_board_saved_projection_text")
        if len(self.filter_tags) != len(set(self.filter_tags)):
            raise ValueError("work board saved projection duplicate filter tag")
        if len(self.link_contract_refs) != len(set(self.link_contract_refs)):
            raise ValueError("work board saved projection duplicate link contract")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"work board saved projection disabled {disabled[0]}")
        forbidden_flags = {
            "copies_task_lifecycle": self.copies_task_lifecycle,
            "publishing_enabled": self.publishing_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "background_sync_enabled": self.background_sync_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board saved projection enabled {enabled[0]}")
        return self


class WorkBoardDragDropPostureReadModel(BaseModel):
    posture_ref: str = "drag-drop-posture:work-board-exact-approved-reorder"
    safe_summary: str = Field(..., min_length=1, max_length=520)
    local_preview_enabled: bool = True
    keyboard_reorder_preview_enabled: bool = True
    durable_reorder_enabled: bool = True
    backend_mutation_route_available: bool = True
    receipt_created: bool = False
    rollback_available: bool = True
    mutation_route_ref: str = WORK_BOARD_REORDER_ROUTE_REF
    approval_required: bool = True
    exact_scope_required: bool = True
    idempotency_required: bool = True
    safe_disable_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_REORDER_SAFE_DISABLE_REF]
    )
    rollback_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_REORDER_ROLLBACK_REF]
    )
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "WorkBoardDragDropPostureReadModel":
        for ref in [
            self.posture_ref,
            *self.safe_disable_refs,
            *self.rollback_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
        ]:
            validate_task_ref(ref, "work_board_drag_posture_ref")
        validate_safe_task_text(self.safe_summary, "work_board_drag_posture_text")
        validate_safe_task_text(self.mutation_route_ref, "work_board_drag_route_ref")
        if not self.local_preview_enabled:
            raise ValueError("work board local drag preview should be visible")
        if not self.keyboard_reorder_preview_enabled:
            raise ValueError("work board keyboard reorder preview should be visible")
        if self.receipt_created:
            raise ValueError("work board read model cannot claim a receipt was created")
        if self.durable_reorder_enabled != self.backend_mutation_route_available:
            raise ValueError("work board durable route posture drift")
        required_true_flags = {
            "durable_reorder_enabled": self.durable_reorder_enabled,
            "backend_mutation_route_available": self.backend_mutation_route_available,
            "rollback_available": self.rollback_available,
            "approval_required": self.approval_required,
            "exact_scope_required": self.exact_scope_required,
            "idempotency_required": self.idempotency_required,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"work board drag posture disabled {disabled[0]}")
        if not self.safe_disable_refs or not self.rollback_refs:
            raise ValueError("work board durable reorder requires safety refs")
        return self


class WorkBoardReadModel(BaseModel):
    schema_version: Literal["uaa-work-board-read-model.v1"] = (
        "uaa-work-board-read-model.v1"
    )
    contract_ref: str = WORK_BOARD_CONTRACT_REF
    board_ref: str = WORK_BOARD_BOARD_REF
    route_ref: str = WORK_BOARD_ROUTE_REF
    backend_route_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_BACKEND_ROUTE_REF]
    )
    frontend_route_refs: list[str] = Field(
        default_factory=lambda: [WORK_BOARD_FRONTEND_ROUTE_REF]
    )
    cli_inspection_refs: list[str] = Field(default_factory=lambda: [WORK_BOARD_CLI_REF])
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs-ref:founder-command-center-board",
            "docs-ref:current-kanban-board",
            "docs-ref:control-center-frontend-routes",
        ]
    )
    source_label: str = "python_core_work_board_read_model"
    status: BoardStatus = "backend_owned_read_model"
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=640)
    northstar_ref: str = "northstar-ref:uaa-local-first-kanban-cockpit"
    repo_safe_scope: str = Field(..., min_length=1, max_length=640)
    full_strength_goal: str = Field(..., min_length=1, max_length=640)
    columns: list[WorkBoardColumnReadModel] = Field(default_factory=list)
    cards: list[WorkBoardCardReadModel] = Field(default_factory=list)
    saved_projections: list[WorkBoardSavedProjectionReadModel] = Field(
        default_factory=list
    )
    local_task_records: list[WorkBoardLocalTaskReadModel] = Field(default_factory=list)
    blocked_lanes: list[WorkBoardBlockedLaneReadModel] = Field(default_factory=list)
    drag_drop_posture: WorkBoardDragDropPostureReadModel
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=420)
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    non_authoritative_mock_fallback: bool = False
    raw_paths_included: bool = False
    raw_content_included: bool = False
    board_mutation_enabled: bool = False
    durable_drag_drop_enabled: bool = False
    durable_reorder_persistence_enabled: bool = True
    approval_required_for_reorder: bool = True
    reorder_route_ref: str = WORK_BOARD_REORDER_ROUTE_REF
    latest_reorder_receipt_ref: str | None = None
    local_card_create_enabled: bool = True
    local_card_create_contract_available: bool = True
    approval_required_for_card_create: bool = True
    card_create_route_available: bool = True
    card_create_route_ref: str = WORK_BOARD_CARD_CREATE_ROUTE_REF
    latest_card_create_receipt_ref: str | None = None
    local_task_create_enabled: bool = True
    local_task_create_contract_available: bool = True
    approval_required_for_task_create: bool = True
    task_create_route_available: bool = True
    task_create_route_ref: str = WORK_BOARD_TASK_CREATE_ROUTE_REF
    latest_task_create_receipt_ref: str | None = None
    issue_tracker_write_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_board(self) -> "WorkBoardReadModel":
        for ref in [
            self.contract_ref,
            self.board_ref,
            self.route_ref,
            self.northstar_ref,
            *(
                [self.latest_reorder_receipt_ref]
                if self.latest_reorder_receipt_ref
                else []
            ),
            *(
                [self.latest_card_create_receipt_ref]
                if self.latest_card_create_receipt_ref
                else []
            ),
            *(
                [self.latest_task_create_receipt_ref]
                if self.latest_task_create_receipt_ref
                else []
            ),
            *self.docs_refs,
            *self.proof_refs,
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.promotion_path_refs,
            *self.redactions_applied,
        ]:
            validate_task_ref(ref, "work_board_ref")
        for value in (
            self.backend_route_refs
            + self.frontend_route_refs
            + self.cli_inspection_refs
            + [
                self.source_label,
                self.status,
                self.title,
                self.safe_summary,
                self.repo_safe_scope,
                self.full_strength_goal,
                self.next_safe_action,
            ]
        ):
            validate_safe_task_text(value, "work_board_text")
        validate_safe_task_text(self.reorder_route_ref, "work_board_reorder_route_ref")
        validate_safe_task_text(
            self.card_create_route_ref,
            "work_board_card_create_route_ref",
        )
        validate_safe_task_text(
            self.task_create_route_ref,
            "work_board_task_create_route_ref",
        )
        column_refs = {column.column_ref for column in self.columns}
        card_refs = {card.card_ref for card in self.cards}
        if not column_refs:
            raise ValueError("work board requires columns")
        if not card_refs:
            raise ValueError("work board requires cards")
        for card in self.cards:
            if card.column_ref not in column_refs:
                raise ValueError("work board card references missing column")
        for record in self.local_task_records:
            if record.card_ref not in card_refs:
                raise ValueError("work board local task references missing card")
        for column in self.columns:
            if not set(column.card_refs).issubset(card_refs):
                raise ValueError("work board column references missing card")
        card_column_pairs = {
            (card.card_ref, card.column_ref) for card in self.cards
        }
        for column in self.columns:
            for card_ref in column.card_refs:
                if (card_ref, column.column_ref) not in card_column_pairs:
                    raise ValueError("work board column card ordering drifted")
        projection_refs = [
            projection.projection_ref for projection in self.saved_projections
        ]
        if len(projection_refs) != len(set(projection_refs)):
            raise ValueError("work board duplicate saved projection ref")
        social_projection = next(
            (
                projection
                for projection in self.saved_projections
                if projection.projection_ref == WORK_BOARD_SOCIAL_CONTENT_PROJECTION_REF
            ),
            None,
        )
        if social_projection is None:
            raise ValueError("work board Social Content saved projection missing")
        if (
            social_projection.contract_ref
            != WORK_BOARD_SOCIAL_CONTENT_PROJECTION_CONTRACT_REF
            or social_projection.label != "Social Content"
            or social_projection.filter_tags != [WORK_BOARD_SOCIAL_CONTENT_FILTER_TAG]
        ):
            raise ValueError("work board Social Content saved projection drifted")
        if not any(
            set(social_projection.filter_tags).issubset(set(card.tags))
            for card in self.cards
        ):
            raise ValueError(
                "work board Social Content projection has no matching card"
            )
        if not set(WORK_BOARD_REQUIRED_BLOCKED_REFS).issubset(
            self.blocked_authority_refs
        ):
            raise ValueError("work board missing required blocker refs")
        required_true_flags = {
            "backend_owned": self.backend_owned,
            "read_only": self.read_only,
            "safe_refs_only": self.safe_refs_only,
        }
        disabled = [name for name, value in required_true_flags.items() if not value]
        if disabled:
            raise ValueError(f"work board disabled {disabled[0]}")
        forbidden_flags = {
            "raw_paths_included": self.raw_paths_included,
            "raw_content_included": self.raw_content_included,
            "board_mutation_enabled": self.board_mutation_enabled,
            "durable_drag_drop_enabled": self.durable_drag_drop_enabled,
            "issue_tracker_write_enabled": self.issue_tracker_write_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "shell_subprocess_execution_enabled": (
                self.shell_subprocess_execution_enabled
            ),
            "browser_automation_enabled": self.browser_automation_enabled,
            "background_autonomy_enabled": self.background_autonomy_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in forbidden_flags.items() if value]
        if enabled:
            raise ValueError(f"work board enabled {enabled[0]}")
        if not self.durable_reorder_persistence_enabled:
            raise ValueError("work board durable reorder persistence lane missing")
        if not self.approval_required_for_reorder:
            raise ValueError("work board reorder must require approval")
        if not self.local_card_create_enabled:
            raise ValueError("work board exact local card create lane missing")
        if not self.local_card_create_contract_available:
            raise ValueError("work board exact local card create contract missing")
        if not self.approval_required_for_card_create:
            raise ValueError("work board card create must require approval")
        if not self.card_create_route_available:
            raise ValueError("work board card create route must remain visible")
        if self.card_create_route_ref != WORK_BOARD_CARD_CREATE_ROUTE_REF:
            raise ValueError("work board card create route ref mismatch")
        if not self.local_task_create_enabled:
            raise ValueError("work board exact local task create lane missing")
        if not self.local_task_create_contract_available:
            raise ValueError("work board exact local task create contract missing")
        if not self.approval_required_for_task_create:
            raise ValueError("work board task create must require approval")
        if not self.task_create_route_available:
            raise ValueError("work board task create route must remain visible")
        if self.task_create_route_ref != WORK_BOARD_TASK_CREATE_ROUTE_REF:
            raise ValueError("work board task create route ref mismatch")
        validate_safe_task_payload(self.model_dump(mode="json"), "work_board")
        return self


class WorkBoardStorageConflictError(RuntimeError):
    pass


class WorkBoardStorageError(RuntimeError):
    pass


class WorkBoardApprovalError(RuntimeError):
    def __init__(
        self,
        reason_refs: list[str],
        *,
        required_refs: dict[str, str] | None = None,
    ) -> None:
        super().__init__("WORK_BOARD_REORDER_APPROVAL_DENIED")
        self.reason_refs = reason_refs
        self.required_refs = required_refs or {}


class WorkBoardAuthorityError(RuntimeError):
    def __init__(
        self,
        reason_refs: list[str],
        *,
        required_refs: dict[str, str] | None = None,
    ) -> None:
        super().__init__("WORK_BOARD_AUTHORITY_DENIED")
        self.reason_refs = reason_refs
        self.required_refs = required_refs or {}


def active_work_board_authority_leases() -> list[AuthorityLease]:
    active = AuthorityLeaseStore().list_leases(active_only=True)
    return active or build_default_authority_leases()


def _layout_from_columns(
    columns: list[WorkBoardColumnReadModel],
) -> dict[str, list[str]]:
    return {column.column_ref: list(column.card_refs) for column in columns}


def _validate_layout_against_board(
    layout: dict[str, list[str]],
    *,
    columns: list[WorkBoardColumnReadModel],
    cards: list[WorkBoardCardReadModel],
) -> None:
    column_refs = {column.column_ref for column in columns}
    card_refs = {card.card_ref for card in cards}
    if set(layout) != column_refs:
        raise WorkBoardStorageError("WORK_BOARD_STATE_COLUMN_SET_INVALID")
    seen_cards: list[str] = []
    for column in columns:
        refs = layout.get(column.column_ref)
        if refs is None:
            raise WorkBoardStorageError("WORK_BOARD_STATE_COLUMN_MISSING")
        if len(refs) > column.wip_limit:
            raise WorkBoardStorageError("WORK_BOARD_STATE_COLUMN_WIP_EXCEEDED")
        seen_cards.extend(refs)
    if len(seen_cards) != len(set(seen_cards)):
        raise WorkBoardStorageError("WORK_BOARD_STATE_DUPLICATE_CARD")
    if set(seen_cards) != card_refs:
        raise WorkBoardStorageError("WORK_BOARD_STATE_CARD_SET_INVALID")


def _order_ref(layout: dict[str, list[str]]) -> str:
    return _hash_ref("work-board-order-ref", layout)


def _local_card_ref(
    request: WorkBoardCardCreateRequest,
    *,
    idempotency_ref: str,
) -> str:
    return _hash_ref(
        "work-board-card:local",
        {
            "board_ref": request.board_ref,
            "column_ref": request.column_ref,
            "idempotency_ref": idempotency_ref,
            "safe_summary": request.safe_summary,
            "title": request.title,
        },
    )


def _local_task_ref(
    *,
    card_ref: str,
    idempotency_ref: str,
) -> str:
    return _hash_ref(
        "work-board-local-task",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "card_ref": card_ref,
            "idempotency_ref": idempotency_ref,
        },
    )


def _card_create_payload_ref(
    request: WorkBoardCardCreateRequest,
    *,
    card_ref: str,
    idempotency_ref: str,
    new_order_ref: str,
    previous_order_ref: str,
) -> str:
    return _hash_ref(
        "work-board-card-create-payload-ref",
        {
            "board_ref": request.board_ref,
            "card_ref": card_ref,
            "column_ref": request.column_ref,
            "decision": request.decision,
            "decision_reason_ref": request.decision_reason_ref,
            "idempotency_ref": idempotency_ref,
            "metadata_refs": request.metadata_refs,
            "new_order_ref": new_order_ref,
            "previous_order_ref": previous_order_ref,
            "priority": request.priority,
            "safe_summary": request.safe_summary,
            "tags": request.tags,
            "title": request.title,
        },
    )


def _task_create_payload_ref(
    request: WorkBoardTaskCreateRequest,
    *,
    idempotency_ref: str,
    local_task_ref: str,
) -> str:
    return _hash_ref(
        "work-board-task-create-payload-ref",
        {
            "board_ref": request.board_ref,
            "card_ref": request.card_ref,
            "decision": request.decision,
            "decision_reason_ref": request.decision_reason_ref,
            "idempotency_ref": idempotency_ref,
            "local_task_ref": local_task_ref,
            "metadata_refs": request.metadata_refs,
        },
    )


def _normalized_layout_from_request(
    request: WorkBoardReorderRequest,
    *,
    columns: list[WorkBoardColumnReadModel],
    cards: list[WorkBoardCardReadModel],
) -> dict[str, list[str]]:
    if request.board_ref != WORK_BOARD_BOARD_REF:
        raise ValueError("work board reorder board ref mismatch")
    column_by_ref = {column.column_ref: column for column in columns}
    card_refs = {card.card_ref for card in cards}
    request_column_refs = [column.column_ref for column in request.columns]
    if set(request_column_refs) != set(column_by_ref):
        raise ValueError("work board reorder must include every backend column")
    seen_cards: list[str] = []
    layout_by_ref = {column.column_ref: list(column.card_refs) for column in request.columns}
    for column_ref, refs in layout_by_ref.items():
        if len(refs) > column_by_ref[column_ref].wip_limit:
            raise ValueError("work board reorder exceeds column wip limit")
        seen_cards.extend(refs)
    if len(seen_cards) != len(set(seen_cards)):
        raise ValueError("work board reorder contains duplicate cards")
    if set(seen_cards) != card_refs:
        raise ValueError("work board reorder must include every backend card exactly once")
    return {column.column_ref: layout_by_ref[column.column_ref] for column in columns}


def _local_card_from_request(
    request: WorkBoardCardCreateRequest,
    *,
    card_ref: str,
) -> WorkBoardCardReadModel:
    return WorkBoardCardReadModel(
        card_ref=card_ref,
        title=request.title,
        safe_summary=request.safe_summary,
        column_ref=request.column_ref,
        priority=request.priority,
        authority_state="proposal_only",
        owner_ref="owner-ref:local-operator",
        progress_label="Created",
        proof_refs=[WORK_BOARD_CARD_CREATE_PROOF_REF],
        evidence_refs=[WORK_BOARD_CARD_CREATE_EVIDENCE_REF],
        blocker_refs=[WORK_BOARD_BLOCKED_CARD_ARCHIVE_ASSIGNMENT_REF],
        surface_refs=[WORK_BOARD_ROUTE_REF],
        cli_inspection_refs=[WORK_BOARD_CARD_CREATE_CLI_REF],
        tags=list(dict.fromkeys([*request.tags, "local-card"])),
        raw_path_included=False,
        raw_content_included=False,
        mutation_enabled=False,
        drag_persistence_enabled=False,
    )


def _local_task_record_from_card(
    card: WorkBoardCardReadModel,
    *,
    local_task_ref: str,
    receipt_ref: str,
) -> WorkBoardLocalTaskReadModel:
    return WorkBoardLocalTaskReadModel(
        local_task_ref=local_task_ref,
        card_ref=card.card_ref,
        title=card.title,
        safe_summary=(
            "Local Work Board task record created from a selected card. "
            "It records safe refs only and does not execute work or sync external systems."
        ),
        receipt_ref=receipt_ref,
        proof_refs=[WORK_BOARD_TASK_CREATE_PROOF_REF],
        evidence_refs=[WORK_BOARD_TASK_CREATE_EVIDENCE_REF],
        blocker_refs=[
            WORK_BOARD_BLOCKED_CARD_ARCHIVE_ASSIGNMENT_REF,
            "blocked-state:work-board-no-issue-tracker-write",
            "blocked-state:work-board-no-connector-write",
            "blocked-state:work-board-no-shell-subprocess",
            "blocked-state:work-board-no-browser-automation",
            "blocked-state:work-board-no-background-autonomy",
            "blocked-state:work-board-no-production-authority",
        ],
        cli_inspection_refs=[WORK_BOARD_TASK_CREATE_CLI_REF],
    )


def _apply_layout(
    *,
    columns: list[WorkBoardColumnReadModel],
    cards: list[WorkBoardCardReadModel],
    layout: dict[str, list[str]],
) -> tuple[list[WorkBoardColumnReadModel], list[WorkBoardCardReadModel]]:
    column_for_card: dict[str, str] = {}
    for column_ref, card_refs in layout.items():
        for card_ref in card_refs:
            column_for_card[card_ref] = column_ref
    return (
        [
            column.model_copy(update={"card_refs": list(layout[column.column_ref])})
            for column in columns
        ],
        [
            card.model_copy(
                update={"column_ref": column_for_card.get(card.card_ref, card.column_ref)}
            )
            for card in cards
        ],
    )


def _work_board_exact_scope_ref(
    *,
    previous_order_ref: str,
    new_order_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-approval-scope-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "previous_order_ref": previous_order_ref,
            "new_order_ref": new_order_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "route_ref": WORK_BOARD_REORDER_ROUTE_REF,
        },
    )


def _work_board_card_create_exact_scope_ref(
    *,
    card_ref: str,
    new_order_ref: str,
    payload_fingerprint_ref: str,
    previous_order_ref: str,
) -> str:
    return _hash_ref(
        "work-board-card-create-scope-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "card_ref": card_ref,
            "new_order_ref": new_order_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "previous_order_ref": previous_order_ref,
            "route_ref": WORK_BOARD_CARD_CREATE_ROUTE_REF,
        },
    )


def _work_board_task_create_exact_scope_ref(
    *,
    card_ref: str,
    local_task_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-task-create-scope-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "card_ref": card_ref,
            "local_task_ref": local_task_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "route_ref": WORK_BOARD_TASK_CREATE_ROUTE_REF,
        },
    )


def _expected_work_board_approval_ref(
    *,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-approval-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "requested_action": WORK_BOARD_REORDER_REQUESTED_ACTION,
        },
    )


def _expected_work_board_card_create_approval_ref(
    *,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-card-create-approval-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "requested_action": WORK_BOARD_CARD_CREATE_REQUESTED_ACTION,
        },
    )


def _expected_work_board_task_create_approval_ref(
    *,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-task-create-approval-ref",
        {
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
            "requested_action": WORK_BOARD_TASK_CREATE_REQUESTED_ACTION,
        },
    )


def _expected_work_board_action_envelope_ref(
    *,
    approval_ref: str,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-action-envelope-ref",
        {
            "approval_ref": approval_ref,
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
        },
    )


def _expected_work_board_card_create_action_envelope_ref(
    *,
    approval_ref: str,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-card-create-action-envelope-ref",
        {
            "approval_ref": approval_ref,
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
        },
    )


def _expected_work_board_task_create_action_envelope_ref(
    *,
    approval_ref: str,
    exact_scope_ref: str,
    payload_fingerprint_ref: str,
) -> str:
    return _hash_ref(
        "work-board-task-create-action-envelope-ref",
        {
            "approval_ref": approval_ref,
            "board_ref": WORK_BOARD_BOARD_REF,
            "decision": "approve",
            "exact_scope_ref": exact_scope_ref,
            "payload_fingerprint_ref": payload_fingerprint_ref,
        },
    )


def _work_board_approval_request(
    *,
    action_envelope_ref: str,
    exact_scope_ref: str,
    idempotency_ref: str,
    new_order_ref: str,
    payload_fingerprint_ref: str,
    previous_order_ref: str,
) -> ApprovalRequest:
    request_ref = _hash_ref(
        "approval-request-ref",
        {
            "action_envelope_ref": action_envelope_ref,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_ref": idempotency_ref,
        },
    )
    run_ref = _hash_ref(
        "run-ref",
        {
            "operation": WORK_BOARD_REORDER_REQUESTED_ACTION,
            "board_ref": WORK_BOARD_BOARD_REF,
        },
    )
    return ApprovalRequest(
        approval_request_id=request_ref,
        run_id=run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=WORK_BOARD_BOARD_REF,
        actor_context=_work_board_actor_context(),
        requested_action=WORK_BOARD_REORDER_REQUESTED_ACTION,
        purpose="Approve one exact local Work Board reorder.",
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="work_board_reorder",
            requires_redaction=True,
        ),
        resource_refs=[
            WORK_BOARD_BOARD_REF,
            WORK_BOARD_REORDER_ROUTE_REF,
            action_envelope_ref,
            exact_scope_ref,
            payload_fingerprint_ref,
            previous_order_ref,
            new_order_ref,
            WORK_BOARD_REORDER_SAFE_DISABLE_REF,
            WORK_BOARD_REORDER_ROLLBACK_REF,
            idempotency_ref,
        ],
        event_ref=_hash_ref(
            "event-ref",
            {
                "operation": "work-board-reorder-approval",
                "idempotency_ref": idempotency_ref,
            },
        ),
        trace_id=_hash_ref("trace-ref", {"operation": "work-board-reorder"}),
    )


def _work_board_card_create_approval_request(
    *,
    action_envelope_ref: str,
    card_ref: str,
    exact_scope_ref: str,
    idempotency_ref: str,
    new_order_ref: str,
    payload_fingerprint_ref: str,
    previous_order_ref: str,
) -> ApprovalRequest:
    request_ref = _hash_ref(
        "approval-request-ref",
        {
            "action_envelope_ref": action_envelope_ref,
            "card_ref": card_ref,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_ref": idempotency_ref,
        },
    )
    run_ref = _hash_ref(
        "run-ref",
        {
            "operation": WORK_BOARD_CARD_CREATE_REQUESTED_ACTION,
            "board_ref": WORK_BOARD_BOARD_REF,
            "card_ref": card_ref,
        },
    )
    return ApprovalRequest(
        approval_request_id=request_ref,
        run_id=run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=WORK_BOARD_BOARD_REF,
        actor_context=_work_board_actor_context(),
        requested_action=WORK_BOARD_CARD_CREATE_REQUESTED_ACTION,
        purpose="Approve one exact local Work Board card create.",
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="work_board_card_create",
            requires_redaction=True,
        ),
        resource_refs=[
            WORK_BOARD_BOARD_REF,
            WORK_BOARD_CARD_CREATE_ROUTE_REF,
            card_ref,
            action_envelope_ref,
            exact_scope_ref,
            payload_fingerprint_ref,
            previous_order_ref,
            new_order_ref,
            WORK_BOARD_CARD_CREATE_SAFE_DISABLE_REF,
            WORK_BOARD_CARD_CREATE_ROLLBACK_REF,
            idempotency_ref,
        ],
        event_ref=_hash_ref(
            "event-ref",
            {
                "operation": "work-board-card-create-approval",
                "idempotency_ref": idempotency_ref,
            },
        ),
        trace_id=_hash_ref(
            "trace-ref",
            {"operation": "work-board-card-create", "card_ref": card_ref},
        ),
    )


def _work_board_task_create_approval_request(
    *,
    action_envelope_ref: str,
    card_ref: str,
    exact_scope_ref: str,
    idempotency_ref: str,
    local_task_ref: str,
    payload_fingerprint_ref: str,
) -> ApprovalRequest:
    request_ref = _hash_ref(
        "approval-request-ref",
        {
            "action_envelope_ref": action_envelope_ref,
            "card_ref": card_ref,
            "exact_scope_ref": exact_scope_ref,
            "idempotency_ref": idempotency_ref,
            "local_task_ref": local_task_ref,
        },
    )
    run_ref = _hash_ref(
        "run-ref",
        {
            "operation": WORK_BOARD_TASK_CREATE_REQUESTED_ACTION,
            "board_ref": WORK_BOARD_BOARD_REF,
            "card_ref": card_ref,
            "local_task_ref": local_task_ref,
        },
    )
    return ApprovalRequest(
        approval_request_id=request_ref,
        run_id=run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=WORK_BOARD_BOARD_REF,
        actor_context=_work_board_actor_context(),
        requested_action=WORK_BOARD_TASK_CREATE_REQUESTED_ACTION,
        purpose="Approve one exact local Work Board task record create.",
        risk_level=ApprovalRiskLevel.low,
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="work_board_task_create",
            requires_redaction=True,
        ),
        resource_refs=[
            WORK_BOARD_BOARD_REF,
            WORK_BOARD_TASK_CREATE_ROUTE_REF,
            card_ref,
            local_task_ref,
            action_envelope_ref,
            exact_scope_ref,
            payload_fingerprint_ref,
            WORK_BOARD_TASK_CREATE_SAFE_DISABLE_REF,
            WORK_BOARD_TASK_CREATE_ROLLBACK_REF,
            idempotency_ref,
        ],
        event_ref=_hash_ref(
            "event-ref",
            {
                "operation": "work-board-task-create-approval",
                "idempotency_ref": idempotency_ref,
            },
        ),
        trace_id=_hash_ref(
            "trace-ref",
            {"operation": "work-board-task-create", "local_task_ref": local_task_ref},
        ),
    )


def prepare_work_board_reorder_approval(
    request: WorkBoardReorderRequest,
    *,
    columns: list[WorkBoardColumnReadModel],
    cards: list[WorkBoardCardReadModel],
    idempotency_ref: str,
    current_layout: dict[str, list[str]] | None = None,
) -> WorkBoardReorderApprovalPreview:
    validate_task_ref(idempotency_ref, "work_board_reorder_idempotency_ref")
    layout = current_layout or _layout_from_columns(columns)
    new_layout = _normalized_layout_from_request(
        request,
        columns=columns,
        cards=cards,
    )
    previous_order_ref = _order_ref(layout)
    new_order_ref = _order_ref(new_layout)
    payload_fingerprint_ref = _hash_ref(
        "work-board-reorder-payload-ref",
        {
            "board_ref": request.board_ref,
            "columns": new_layout,
            "decision_reason_ref": request.decision_reason_ref,
            "metadata_refs": request.metadata_refs,
        },
    )
    exact_scope_ref = _work_board_exact_scope_ref(
        previous_order_ref=previous_order_ref,
        new_order_ref=new_order_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    expected_approval_ref = _expected_work_board_approval_ref(
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    action_envelope_ref = _expected_work_board_action_envelope_ref(
        approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    approval_request = _work_board_approval_request(
        action_envelope_ref=action_envelope_ref,
        exact_scope_ref=exact_scope_ref,
        idempotency_ref=idempotency_ref,
        new_order_ref=new_order_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        previous_order_ref=previous_order_ref,
    )
    return WorkBoardReorderApprovalPreview(
        approval_request=approval_request,
        expected_approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        action_envelope_ref=action_envelope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        previous_order_ref=previous_order_ref,
        new_order_ref=new_order_ref,
    )


def prepare_work_board_card_create_approval(
    request: WorkBoardCardCreateRequest,
    *,
    columns: list[WorkBoardColumnReadModel],
    cards: list[WorkBoardCardReadModel],
    idempotency_ref: str,
    current_layout: dict[str, list[str]] | None = None,
) -> WorkBoardCardCreateApprovalPreview:
    validate_task_ref(idempotency_ref, "work_board_card_create_idempotency_ref")
    column_by_ref = {column.column_ref: column for column in columns}
    if request.column_ref not in column_by_ref:
        raise ValueError("work board card create column ref missing")
    layout = current_layout or _layout_from_columns(columns)
    card_ref = _local_card_ref(request, idempotency_ref=idempotency_ref)
    if card_ref in {card.card_ref for card in cards}:
        raise WorkBoardStorageConflictError("WORK_BOARD_CARD_CREATE_REF_CONFLICT")
    next_refs = [*layout.get(request.column_ref, []), card_ref]
    if len(next_refs) > column_by_ref[request.column_ref].wip_limit:
        raise ValueError("work board card create exceeds column wip limit")
    new_layout = {column.column_ref: list(layout.get(column.column_ref, [])) for column in columns}
    new_layout[request.column_ref] = next_refs
    previous_order_ref = _order_ref(layout)
    new_order_ref = _order_ref(new_layout)
    payload_fingerprint_ref = _card_create_payload_ref(
        request,
        card_ref=card_ref,
        idempotency_ref=idempotency_ref,
        new_order_ref=new_order_ref,
        previous_order_ref=previous_order_ref,
    )
    exact_scope_ref = _work_board_card_create_exact_scope_ref(
        card_ref=card_ref,
        new_order_ref=new_order_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        previous_order_ref=previous_order_ref,
    )
    expected_approval_ref = _expected_work_board_card_create_approval_ref(
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    action_envelope_ref = _expected_work_board_card_create_action_envelope_ref(
        approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    approval_request = _work_board_card_create_approval_request(
        action_envelope_ref=action_envelope_ref,
        card_ref=card_ref,
        exact_scope_ref=exact_scope_ref,
        idempotency_ref=idempotency_ref,
        new_order_ref=new_order_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        previous_order_ref=previous_order_ref,
    )
    return WorkBoardCardCreateApprovalPreview(
        approval_request=approval_request,
        expected_approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        action_envelope_ref=action_envelope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        previous_order_ref=previous_order_ref,
        new_order_ref=new_order_ref,
        card_ref=card_ref,
    )


def prepare_work_board_task_create_approval(
    request: WorkBoardTaskCreateRequest,
    *,
    cards: list[WorkBoardCardReadModel],
    idempotency_ref: str,
) -> WorkBoardTaskCreateApprovalPreview:
    validate_task_ref(idempotency_ref, "work_board_task_create_idempotency_ref")
    card_by_ref = {card.card_ref: card for card in cards}
    if request.card_ref not in card_by_ref:
        raise ValueError("work board task create card ref missing")
    local_task_ref = _local_task_ref(
        card_ref=request.card_ref,
        idempotency_ref=idempotency_ref,
    )
    payload_fingerprint_ref = _task_create_payload_ref(
        request,
        idempotency_ref=idempotency_ref,
        local_task_ref=local_task_ref,
    )
    exact_scope_ref = _work_board_task_create_exact_scope_ref(
        card_ref=request.card_ref,
        local_task_ref=local_task_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    expected_approval_ref = _expected_work_board_task_create_approval_ref(
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    action_envelope_ref = _expected_work_board_task_create_action_envelope_ref(
        approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    approval_request = _work_board_task_create_approval_request(
        action_envelope_ref=action_envelope_ref,
        card_ref=request.card_ref,
        exact_scope_ref=exact_scope_ref,
        idempotency_ref=idempotency_ref,
        local_task_ref=local_task_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
    )
    return WorkBoardTaskCreateApprovalPreview(
        approval_request=approval_request,
        expected_approval_ref=expected_approval_ref,
        exact_scope_ref=exact_scope_ref,
        action_envelope_ref=action_envelope_ref,
        payload_fingerprint_ref=payload_fingerprint_ref,
        card_ref=request.card_ref,
        local_task_ref=local_task_ref,
    )


def _validate_work_board_approval(
    *,
    request: WorkBoardReorderRequest,
    action_envelope_ref: str,
    exact_scope_ref: str,
    expected_approval_ref: str,
    approval_request: ApprovalRequest,
    approval_authority: LocalApprovalAuthority | None,
    idempotency_ref: str,
    new_order_ref: str,
    payload_fingerprint_ref: str,
    previous_order_ref: str,
) -> tuple[str, str, str]:
    reason_refs: list[str] = []
    if request.exact_scope_ref is None:
        reason_refs.append("blocked-state:work-board-reorder-exact-scope-required")
    elif request.exact_scope_ref != exact_scope_ref:
        reason_refs.append("blocked-state:work-board-reorder-exact-scope-mismatch")
    if request.action_envelope_ref is None:
        reason_refs.append("blocked-state:work-board-reorder-action-envelope-required")
    elif request.action_envelope_ref != action_envelope_ref:
        reason_refs.append("blocked-state:work-board-reorder-action-envelope-mismatch")
    if request.approval_ref is None:
        reason_refs.append("blocked-state:work-board-reorder-approval-required")
    elif request.approval_ref != expected_approval_ref:
        reason_refs.append("blocked-state:work-board-reorder-approval-ref-mismatch")
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
            },
        )
    approval_ref = request.approval_ref
    authority = approval_authority or LocalApprovalAuthority()
    authority.create_request(approval_request)
    decision = authority.validate_for_request(approval_request, approval_ref)
    approval_decision_ref = _hash_ref(
        "approval-decision-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-reorder-approval",
        },
    )
    approval_validation_ref = _hash_ref(
        "approval-validation-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-reorder-approval",
        },
    )
    if not decision.allowed:
        reason_refs.append("blocked-state:work-board-reorder-backend-approval-missing")
        reason_refs.extend(
            f"approval-reason-ref:{reason}" for reason in decision.reason_codes
        )
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
            },
        )
    return approval_ref, approval_decision_ref, approval_validation_ref


def _validate_work_board_card_create_approval(
    *,
    request: WorkBoardCardCreateRequest,
    action_envelope_ref: str,
    card_ref: str,
    exact_scope_ref: str,
    expected_approval_ref: str,
    approval_request: ApprovalRequest,
    approval_authority: LocalApprovalAuthority | None,
    idempotency_ref: str,
) -> tuple[str, str, str]:
    reason_refs: list[str] = []
    if request.exact_scope_ref is None:
        reason_refs.append("blocked-state:work-board-card-create-exact-scope-required")
    elif request.exact_scope_ref != exact_scope_ref:
        reason_refs.append("blocked-state:work-board-card-create-exact-scope-mismatch")
    if request.action_envelope_ref is None:
        reason_refs.append(
            "blocked-state:work-board-card-create-action-envelope-required"
        )
    elif request.action_envelope_ref != action_envelope_ref:
        reason_refs.append(
            "blocked-state:work-board-card-create-action-envelope-mismatch"
        )
    if request.approval_ref is None:
        reason_refs.append("blocked-state:work-board-card-create-approval-required")
    elif request.approval_ref != expected_approval_ref:
        reason_refs.append("blocked-state:work-board-card-create-approval-ref-mismatch")
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
                "card_ref": card_ref,
            },
        )
    approval_ref = request.approval_ref
    authority = approval_authority or LocalApprovalAuthority()
    authority.create_request(approval_request)
    decision = authority.validate_for_request(approval_request, approval_ref)
    approval_decision_ref = _hash_ref(
        "approval-decision-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-card-create-approval",
        },
    )
    approval_validation_ref = _hash_ref(
        "approval-validation-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-card-create-approval",
        },
    )
    if not decision.allowed:
        reason_refs.append(
            "blocked-state:work-board-card-create-backend-approval-missing"
        )
        reason_refs.extend(
            f"approval-reason-ref:{reason}" for reason in decision.reason_codes
        )
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
                "card_ref": card_ref,
            },
        )
    return approval_ref, approval_decision_ref, approval_validation_ref


def _validate_work_board_task_create_approval(
    *,
    request: WorkBoardTaskCreateRequest,
    action_envelope_ref: str,
    exact_scope_ref: str,
    expected_approval_ref: str,
    approval_request: ApprovalRequest,
    approval_authority: LocalApprovalAuthority | None,
    idempotency_ref: str,
    local_task_ref: str,
) -> tuple[str, str, str]:
    reason_refs: list[str] = []
    if request.exact_scope_ref is None:
        reason_refs.append("blocked-state:work-board-task-create-exact-scope-required")
    elif request.exact_scope_ref != exact_scope_ref:
        reason_refs.append("blocked-state:work-board-task-create-exact-scope-mismatch")
    if request.action_envelope_ref is None:
        reason_refs.append(
            "blocked-state:work-board-task-create-action-envelope-required"
        )
    elif request.action_envelope_ref != action_envelope_ref:
        reason_refs.append(
            "blocked-state:work-board-task-create-action-envelope-mismatch"
        )
    if request.approval_ref is None:
        reason_refs.append("blocked-state:work-board-task-create-approval-required")
    elif request.approval_ref != expected_approval_ref:
        reason_refs.append("blocked-state:work-board-task-create-approval-ref-mismatch")
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
                "local_task_ref": local_task_ref,
            },
        )
    approval_ref = request.approval_ref
    authority = approval_authority or LocalApprovalAuthority()
    authority.create_request(approval_request)
    decision = authority.validate_for_request(approval_request, approval_ref)
    approval_decision_ref = _hash_ref(
        "approval-decision-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-task-create-approval",
        },
    )
    approval_validation_ref = _hash_ref(
        "approval-validation-ref",
        {
            "approval_ref": approval_ref,
            "idempotency_ref": idempotency_ref,
            "operation": "work-board-task-create-approval",
        },
    )
    if not decision.allowed:
        reason_refs.append(
            "blocked-state:work-board-task-create-backend-approval-missing"
        )
        reason_refs.extend(
            f"approval-reason-ref:{reason}" for reason in decision.reason_codes
        )
    if reason_refs:
        raise WorkBoardApprovalError(
            list(dict.fromkeys(reason_refs)),
            required_refs={
                "approval_ref": expected_approval_ref,
                "exact_scope_ref": exact_scope_ref,
                "action_envelope_ref": action_envelope_ref,
                "local_task_ref": local_task_ref,
            },
        )
    return approval_ref, approval_decision_ref, approval_validation_ref


def _validate_work_board_authority(
    *,
    action_ref: str,
    route_ref: str,
    active_authority_leases: list[AuthorityLease] | None,
    approval_authority: LocalApprovalAuthority | None = None,
):
    rollback_refs = {
        WORK_BOARD_REORDER_ROUTE_REF: WORK_BOARD_REORDER_ROLLBACK_REF,
        WORK_BOARD_CARD_CREATE_ROUTE_REF: WORK_BOARD_CARD_CREATE_ROLLBACK_REF,
        WORK_BOARD_TASK_CREATE_ROUTE_REF: WORK_BOARD_TASK_CREATE_ROLLBACK_REF,
    }
    safe_disable_refs = {
        WORK_BOARD_REORDER_ROUTE_REF: WORK_BOARD_REORDER_SAFE_DISABLE_REF,
        WORK_BOARD_CARD_CREATE_ROUTE_REF: WORK_BOARD_CARD_CREATE_SAFE_DISABLE_REF,
        WORK_BOARD_TASK_CREATE_ROUTE_REF: WORK_BOARD_TASK_CREATE_SAFE_DISABLE_REF,
    }
    action_request = AuthorityActionRequest(
        action_ref=action_ref,
        domain=AuthorityDomain.workspace,
        capability=AuthorityCapability.write,
        safe_summary=(
            "Evaluate Workspace write authority for exact Work Board local mutation."
        ),
        route_ref=route_ref,
        requested_mode=TrustMode.ask_before_changes,
        draft_fallback_available=True,
        rollback_ref=rollback_refs.get(route_ref, WORK_BOARD_TASK_CREATE_ROLLBACK_REF),
        safe_disable_ref=safe_disable_refs.get(
            route_ref,
            WORK_BOARD_TASK_CREATE_SAFE_DISABLE_REF,
        ),
    )
    if active_authority_leases is not None:
        decision = evaluate_authority_request(action_request, active_authority_leases)
    elif approval_authority is not None and approval_authority.list_authority_leases(
        active_only=True
    ):
        decision = approval_authority.evaluate_authority_scope(action_request)
    else:
        decision = evaluate_authority_request(
            action_request,
            active_work_board_authority_leases(),
        )
    if decision.outcome not in {
        AuthorityDecisionOutcome.allow.value,
        AuthorityDecisionOutcome.ask.value,
    }:
        raise WorkBoardAuthorityError(
            [
                *decision.reason_refs,
                "blocked-state:work-board-authority-lease-required",
            ],
            required_refs={
                "authority_decision_ref": decision.decision_ref,
                "required_mode_ref": "authority-mode-ref:ask-before-changes",
                "required_domain_ref": WORK_BOARD_AUTHORITY_DOMAIN_REF,
                "required_capability_ref": WORK_BOARD_AUTHORITY_CAPABILITY_REF,
                "safe_disable_ref": decision.safe_disable_ref,
                "rollback_ref": decision.rollback_ref,
            },
        )
    return decision


class WorkBoardStateStore:
    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> None:
        self.state_dir = state_dir or work_board_state_dir()
        self.state_path = self.state_dir / WORK_BOARD_STATE_FILE
        self.receipts_path = self.state_dir / WORK_BOARD_RECEIPTS_FILE
        self.card_create_receipts_path = (
            self.state_dir / WORK_BOARD_CARD_CREATE_RECEIPTS_FILE
        )
        self.task_create_receipts_path = (
            self.state_dir / WORK_BOARD_TASK_CREATE_RECEIPTS_FILE
        )
        self._active_authority_leases = active_authority_leases

    def load_layout(self) -> dict[str, list[str]] | None:
        if not self.state_path.exists():
            return None
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        validate_safe_task_payload(payload, "work_board_state")
        layout = payload.get("layout")
        if not isinstance(layout, dict):
            raise WorkBoardStorageError("WORK_BOARD_STATE_LAYOUT_INVALID")
        return {
            str(column_ref): [str(card_ref) for card_ref in card_refs]
            for column_ref, card_refs in layout.items()
            if isinstance(card_refs, list)
        }

    def latest_receipt(self) -> WorkBoardReorderReceipt | None:
        if not self.state_path.exists():
            return None
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        receipt = payload.get("latest_receipt")
        if not isinstance(receipt, dict):
            return None
        return WorkBoardReorderReceipt(**receipt)

    def load_local_cards(self) -> list[WorkBoardCardReadModel]:
        if not self.state_path.exists():
            return []
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        validate_safe_task_payload(payload, "work_board_state")
        local_cards = payload.get("local_cards", [])
        if not isinstance(local_cards, list):
            raise WorkBoardStorageError("WORK_BOARD_STATE_LOCAL_CARDS_INVALID")
        return [
            WorkBoardCardReadModel(**card)
            for card in local_cards
            if isinstance(card, dict)
        ]

    def latest_card_create_receipt(self) -> WorkBoardCardCreateReceipt | None:
        if not self.state_path.exists():
            return None
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        receipt = payload.get("latest_card_create_receipt")
        if not isinstance(receipt, dict):
            return None
        return WorkBoardCardCreateReceipt(**receipt)

    def load_local_task_records(self) -> list[WorkBoardLocalTaskReadModel]:
        if not self.state_path.exists():
            return []
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        validate_safe_task_payload(payload, "work_board_state")
        local_task_records = payload.get("local_task_records", [])
        if not isinstance(local_task_records, list):
            raise WorkBoardStorageError(
                "WORK_BOARD_STATE_LOCAL_TASK_RECORDS_INVALID"
            )
        return [
            WorkBoardLocalTaskReadModel(**record)
            for record in local_task_records
            if isinstance(record, dict)
        ]

    def latest_task_create_receipt(self) -> WorkBoardTaskCreateReceipt | None:
        if not self.state_path.exists():
            return None
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        receipt = payload.get("latest_task_create_receipt")
        if not isinstance(receipt, dict):
            return None
        return WorkBoardTaskCreateReceipt(**receipt)

    def persist_reorder(
        self,
        request: WorkBoardReorderRequest,
        *,
        columns: list[WorkBoardColumnReadModel],
        cards: list[WorkBoardCardReadModel],
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> WorkBoardReorderReceipt:
        validate_task_ref(idempotency_ref, "work_board_reorder_idempotency_ref")
        current_layout = self.load_layout() or _layout_from_columns(columns)
        new_layout = _normalized_layout_from_request(
            request,
            columns=columns,
            cards=cards,
        )
        approval_preview = prepare_work_board_reorder_approval(
            request,
            columns=columns,
            cards=cards,
            idempotency_ref=idempotency_ref,
            current_layout=current_layout,
        )
        replay = self._idempotent_replay(
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
        )
        if replay is not None:
            return replay.model_copy(update={"status": "replayed", "replayed": True})
        approval_ref, approval_decision_ref, approval_validation_ref = (
            _validate_work_board_approval(
                request=request,
                action_envelope_ref=approval_preview.action_envelope_ref,
                exact_scope_ref=approval_preview.exact_scope_ref,
                expected_approval_ref=approval_preview.expected_approval_ref,
                approval_request=approval_preview.approval_request,
                approval_authority=approval_authority,
                idempotency_ref=idempotency_ref,
                new_order_ref=approval_preview.new_order_ref,
                payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
                previous_order_ref=approval_preview.previous_order_ref,
            )
        )
        authority_decision = _validate_work_board_authority(
            action_ref=WORK_BOARD_REORDER_AUTHORITY_ACTION_REF,
            route_ref=WORK_BOARD_REORDER_ROUTE_REF,
            active_authority_leases=self._active_authority_leases,
            approval_authority=approval_authority,
        )
        receipt = WorkBoardReorderReceipt(
            board_ref=WORK_BOARD_BOARD_REF,
            receipt_ref=_hash_ref(
                "receipt:work-board-reorder",
                {
                    "approval_ref": approval_ref,
                    "idempotency_ref": idempotency_ref,
                    "payload_fingerprint_ref": approval_preview.payload_fingerprint_ref,
                },
            ),
            status="applied",
            approval_ref=approval_ref,
            approval_decision_ref=approval_decision_ref,
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            exact_scope_ref=approval_preview.exact_scope_ref,
            action_envelope_ref=approval_preview.action_envelope_ref,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
            previous_order_ref=approval_preview.previous_order_ref,
            new_order_ref=approval_preview.new_order_ref,
            applied_at_ref=_hash_ref("time-ref", utc_now().isoformat()),
            safe_summary=(
                "Exact approved local Work Board reorder persisted safe card refs only."
            ),
        )
        self._write_state(
            new_layout,
            latest_reorder_receipt=receipt,
            latest_card_create_receipt=self.latest_card_create_receipt(),
            latest_task_create_receipt=self.latest_task_create_receipt(),
            local_cards=self.load_local_cards(),
            local_task_records=self.load_local_task_records(),
        )
        self._append_receipt(receipt)
        return receipt

    def persist_card_create(
        self,
        request: WorkBoardCardCreateRequest,
        *,
        columns: list[WorkBoardColumnReadModel],
        cards: list[WorkBoardCardReadModel],
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> WorkBoardCardCreateReceipt:
        validate_task_ref(idempotency_ref, "work_board_card_create_idempotency_ref")
        replay = self._idempotent_card_create_replay_for_request(
            request=request,
            idempotency_ref=idempotency_ref,
        )
        if replay is not None:
            return replay.model_copy(update={"status": "replayed", "replayed": True})
        current_layout = self.load_layout() or _layout_from_columns(columns)
        existing_local_cards = self.load_local_cards()
        existing_card_refs = {card.card_ref for card in cards}
        for local_card in existing_local_cards:
            existing_card_refs.add(local_card.card_ref)
        card_ref = _local_card_ref(request, idempotency_ref=idempotency_ref)
        if card_ref in existing_card_refs:
            raise WorkBoardStorageConflictError("WORK_BOARD_CARD_CREATE_REF_CONFLICT")
        approval_preview = prepare_work_board_card_create_approval(
            request,
            columns=columns,
            cards=[*cards, *existing_local_cards],
            idempotency_ref=idempotency_ref,
            current_layout=current_layout,
        )
        replay = self._idempotent_card_create_replay(
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
        )
        if replay is not None:
            return replay.model_copy(update={"status": "replayed", "replayed": True})
        approval_ref, approval_decision_ref, approval_validation_ref = (
            _validate_work_board_card_create_approval(
                request=request,
                action_envelope_ref=approval_preview.action_envelope_ref,
                card_ref=approval_preview.card_ref,
                exact_scope_ref=approval_preview.exact_scope_ref,
                expected_approval_ref=approval_preview.expected_approval_ref,
                approval_request=approval_preview.approval_request,
                approval_authority=approval_authority,
                idempotency_ref=idempotency_ref,
            )
        )
        authority_decision = _validate_work_board_authority(
            action_ref=WORK_BOARD_CARD_CREATE_AUTHORITY_ACTION_REF,
            route_ref=WORK_BOARD_CARD_CREATE_ROUTE_REF,
            active_authority_leases=self._active_authority_leases,
            approval_authority=approval_authority,
        )
        new_card = _local_card_from_request(request, card_ref=approval_preview.card_ref)
        new_layout = {
            column.column_ref: list(current_layout.get(column.column_ref, []))
            for column in columns
        }
        new_layout[request.column_ref] = [
            *new_layout.get(request.column_ref, []),
            approval_preview.card_ref,
        ]
        receipt = WorkBoardCardCreateReceipt(
            board_ref=WORK_BOARD_BOARD_REF,
            card_ref=approval_preview.card_ref,
            receipt_ref=_hash_ref(
                "receipt:work-board-card-create",
                {
                    "approval_ref": approval_ref,
                    "card_ref": approval_preview.card_ref,
                    "idempotency_ref": idempotency_ref,
                    "payload_fingerprint_ref": approval_preview.payload_fingerprint_ref,
                },
            ),
            status="applied",
            approval_ref=approval_ref,
            approval_decision_ref=approval_decision_ref,
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            exact_scope_ref=approval_preview.exact_scope_ref,
            action_envelope_ref=approval_preview.action_envelope_ref,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
            previous_order_ref=approval_preview.previous_order_ref,
            new_order_ref=approval_preview.new_order_ref,
            applied_at_ref=_hash_ref("time-ref", utc_now().isoformat()),
            safe_summary="Exact approved local Work Board card create persisted safe refs only.",
        )
        self._write_state(
            new_layout,
            latest_reorder_receipt=self.latest_receipt(),
            latest_card_create_receipt=receipt,
            latest_task_create_receipt=self.latest_task_create_receipt(),
            local_cards=[*existing_local_cards, new_card],
            local_task_records=self.load_local_task_records(),
        )
        self._append_card_create_receipt(receipt)
        return receipt

    def persist_task_create(
        self,
        request: WorkBoardTaskCreateRequest,
        *,
        columns: list[WorkBoardColumnReadModel],
        cards: list[WorkBoardCardReadModel],
        idempotency_ref: str,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> WorkBoardTaskCreateReceipt:
        validate_task_ref(idempotency_ref, "work_board_task_create_idempotency_ref")
        replay = self._idempotent_task_create_replay_for_request(
            request=request,
            idempotency_ref=idempotency_ref,
        )
        if replay is not None:
            return replay.model_copy(update={"status": "replayed", "replayed": True})
        card_by_ref = {card.card_ref: card for card in cards}
        if request.card_ref not in card_by_ref:
            raise ValueError("work board task create card ref missing")
        existing_records = self.load_local_task_records()
        if request.card_ref in {record.card_ref for record in existing_records}:
            raise WorkBoardStorageConflictError(
                "WORK_BOARD_TASK_CREATE_CARD_ALREADY_HAS_TASK"
            )
        approval_preview = prepare_work_board_task_create_approval(
            request,
            cards=cards,
            idempotency_ref=idempotency_ref,
        )
        replay = self._idempotent_task_create_replay(
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
        )
        if replay is not None:
            return replay.model_copy(update={"status": "replayed", "replayed": True})
        approval_ref, approval_decision_ref, approval_validation_ref = (
            _validate_work_board_task_create_approval(
                request=request,
                action_envelope_ref=approval_preview.action_envelope_ref,
                exact_scope_ref=approval_preview.exact_scope_ref,
                expected_approval_ref=approval_preview.expected_approval_ref,
                approval_request=approval_preview.approval_request,
                approval_authority=approval_authority,
                idempotency_ref=idempotency_ref,
                local_task_ref=approval_preview.local_task_ref,
            )
        )
        authority_decision = _validate_work_board_authority(
            action_ref=WORK_BOARD_TASK_CREATE_AUTHORITY_ACTION_REF,
            route_ref=WORK_BOARD_TASK_CREATE_ROUTE_REF,
            active_authority_leases=self._active_authority_leases,
            approval_authority=approval_authority,
        )
        receipt_ref = _hash_ref(
            "receipt:work-board-task-create",
            {
                "approval_ref": approval_ref,
                "card_ref": approval_preview.card_ref,
                "idempotency_ref": idempotency_ref,
                "local_task_ref": approval_preview.local_task_ref,
                "payload_fingerprint_ref": approval_preview.payload_fingerprint_ref,
            },
        )
        receipt = WorkBoardTaskCreateReceipt(
            board_ref=WORK_BOARD_BOARD_REF,
            card_ref=approval_preview.card_ref,
            local_task_ref=approval_preview.local_task_ref,
            receipt_ref=receipt_ref,
            status="applied",
            approval_ref=approval_ref,
            approval_decision_ref=approval_decision_ref,
            approval_validation_ref=approval_validation_ref,
            authority_decision_ref=authority_decision.decision_ref,
            authority_decision_outcome=authority_decision.outcome,
            authority_lease_ref=authority_decision.lease_ref,
            exact_scope_ref=approval_preview.exact_scope_ref,
            action_envelope_ref=approval_preview.action_envelope_ref,
            idempotency_ref=idempotency_ref,
            payload_fingerprint_ref=approval_preview.payload_fingerprint_ref,
            applied_at_ref=_hash_ref("time-ref", utc_now().isoformat()),
            safe_summary=(
                "Exact approved local Work Board task record persisted safe refs only; "
                "no task execution or external sync was performed."
            ),
        )
        current_layout = self.load_layout() or _layout_from_columns(columns)
        task_record = _local_task_record_from_card(
            card_by_ref[request.card_ref],
            local_task_ref=approval_preview.local_task_ref,
            receipt_ref=receipt.receipt_ref,
        )
        self._write_state(
            current_layout,
            latest_reorder_receipt=self.latest_receipt(),
            latest_card_create_receipt=self.latest_card_create_receipt(),
            latest_task_create_receipt=receipt,
            local_cards=self.load_local_cards(),
            local_task_records=[*existing_records, task_record],
        )
        self._append_task_create_receipt(receipt)
        return receipt

    def _idempotent_replay(
        self,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> WorkBoardReorderReceipt | None:
        if not self.receipts_path.exists():
            return None
        for line in self.receipts_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            receipt = WorkBoardReorderReceipt(**payload)
            if receipt.idempotency_ref != idempotency_ref:
                continue
            if receipt.payload_fingerprint_ref != payload_fingerprint_ref:
                raise WorkBoardStorageConflictError(
                    "WORK_BOARD_REORDER_IDEMPOTENCY_CONFLICT"
                )
            return receipt
        return None

    def _idempotent_card_create_replay_for_request(
        self,
        *,
        request: WorkBoardCardCreateRequest,
        idempotency_ref: str,
    ) -> WorkBoardCardCreateReceipt | None:
        receipt = self._card_create_receipt_for_idempotency(idempotency_ref)
        if receipt is None:
            return None
        expected_payload_ref = _card_create_payload_ref(
            request,
            card_ref=receipt.card_ref,
            idempotency_ref=idempotency_ref,
            new_order_ref=receipt.new_order_ref,
            previous_order_ref=receipt.previous_order_ref,
        )
        if receipt.payload_fingerprint_ref != expected_payload_ref:
            raise WorkBoardStorageConflictError(
                "WORK_BOARD_CARD_CREATE_IDEMPOTENCY_CONFLICT"
            )
        return receipt

    def _idempotent_card_create_replay(
        self,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> WorkBoardCardCreateReceipt | None:
        receipt = self._card_create_receipt_for_idempotency(idempotency_ref)
        if receipt is None:
            return None
        if receipt.payload_fingerprint_ref != payload_fingerprint_ref:
            raise WorkBoardStorageConflictError(
                "WORK_BOARD_CARD_CREATE_IDEMPOTENCY_CONFLICT"
            )
        return receipt

    def _card_create_receipt_for_idempotency(
        self,
        idempotency_ref: str,
    ) -> WorkBoardCardCreateReceipt | None:
        if not self.card_create_receipts_path.exists():
            return None
        for line in self.card_create_receipts_path.read_text(
            encoding="utf-8"
        ).splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            receipt = WorkBoardCardCreateReceipt(**payload)
            if receipt.idempotency_ref == idempotency_ref:
                return receipt
        return None

    def _idempotent_task_create_replay_for_request(
        self,
        *,
        request: WorkBoardTaskCreateRequest,
        idempotency_ref: str,
    ) -> WorkBoardTaskCreateReceipt | None:
        receipt = self._task_create_receipt_for_idempotency(idempotency_ref)
        if receipt is None:
            return None
        expected_payload_ref = _task_create_payload_ref(
            request,
            idempotency_ref=idempotency_ref,
            local_task_ref=receipt.local_task_ref,
        )
        if receipt.payload_fingerprint_ref != expected_payload_ref:
            raise WorkBoardStorageConflictError(
                "WORK_BOARD_TASK_CREATE_IDEMPOTENCY_CONFLICT"
            )
        return receipt

    def _idempotent_task_create_replay(
        self,
        *,
        idempotency_ref: str,
        payload_fingerprint_ref: str,
    ) -> WorkBoardTaskCreateReceipt | None:
        receipt = self._task_create_receipt_for_idempotency(idempotency_ref)
        if receipt is None:
            return None
        if receipt.payload_fingerprint_ref != payload_fingerprint_ref:
            raise WorkBoardStorageConflictError(
                "WORK_BOARD_TASK_CREATE_IDEMPOTENCY_CONFLICT"
            )
        return receipt

    def _task_create_receipt_for_idempotency(
        self,
        idempotency_ref: str,
    ) -> WorkBoardTaskCreateReceipt | None:
        if not self.task_create_receipts_path.exists():
            return None
        for line in self.task_create_receipts_path.read_text(
            encoding="utf-8"
        ).splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            receipt = WorkBoardTaskCreateReceipt(**payload)
            if receipt.idempotency_ref == idempotency_ref:
                return receipt
        return None

    def _write_state(
        self,
        layout: dict[str, list[str]],
        *,
        latest_reorder_receipt: WorkBoardReorderReceipt | None,
        latest_card_create_receipt: WorkBoardCardCreateReceipt | None,
        latest_task_create_receipt: WorkBoardTaskCreateReceipt | None,
        local_cards: list[WorkBoardCardReadModel],
        local_task_records: list[WorkBoardLocalTaskReadModel],
    ) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "schema_version": "uaa-work-board-state.v1",
            "board_ref": WORK_BOARD_BOARD_REF,
            "layout": layout,
            "layout_order_ref": _order_ref(layout),
            "local_cards": [card.model_dump(mode="json") for card in local_cards],
            "local_task_records": [
                record.model_dump(mode="json") for record in local_task_records
            ],
        }
        if latest_reorder_receipt is not None:
            payload["latest_receipt"] = latest_reorder_receipt.model_dump(mode="json")
        if latest_card_create_receipt is not None:
            payload["latest_card_create_receipt"] = (
                latest_card_create_receipt.model_dump(mode="json")
            )
        if latest_task_create_receipt is not None:
            payload["latest_task_create_receipt"] = (
                latest_task_create_receipt.model_dump(mode="json")
            )
        validate_safe_task_payload(payload, "work_board_state")
        tmp_path = self.state_path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        tmp_path.replace(self.state_path)

    def _append_receipt(self, receipt: WorkBoardReorderReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    receipt.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    def _append_card_create_receipt(self, receipt: WorkBoardCardCreateReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.card_create_receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    receipt.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    def _append_task_create_receipt(self, receipt: WorkBoardTaskCreateReceipt) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.task_create_receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    receipt.model_dump(mode="json"),
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")


def _base_work_board() -> tuple[list[WorkBoardColumnReadModel], list[WorkBoardCardReadModel]]:
    columns = [
        WorkBoardColumnReadModel(
            column_ref="work-board-column:triage",
            label="Triage",
            status="planned",
            safe_summary="New Founder Loop work enters here as safe refs and blocked-authority posture.",
            card_refs=["work-board-card:setup-assistant-hardening"],
            wip_limit=6,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:ready",
            label="Ready",
            status="planned",
            safe_summary="Repo-safe lanes with backend contracts and proof expectations ready for implementation.",
            card_refs=[
                "work-board-card:action-inbox-work-queue",
                "work-board-card:proof-run-spine",
            ],
            wip_limit=5,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:doing",
            label="Doing",
            status="in_progress",
            safe_summary="Active local-first product lanes currently in implementation or hardening.",
            card_refs=[
                "work-board-card:work-board-kanban-shell",
                "work-board-card:daily-loop-productization",
            ],
            wip_limit=3,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:review",
            label="Review",
            status="review",
            safe_summary="Changes that need proof, language, safety, OpenAPI, and UI review before promotion.",
            card_refs=[
                "work-board-card:trust-authority-map",
                WORK_BOARD_SOCIAL_CONTENT_CARD_REF,
            ],
            wip_limit=4,
            blocked_authority_refs=[],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:blocked",
            label="Blocked",
            status="blocked",
            safe_summary="Full-strength lanes visible but blocked until exact authority contracts exist.",
            card_refs=[
                "work-board-card:external-agent-dispatch",
                "work-board-card:connector-write-actions",
            ],
            wip_limit=8,
            blocked_authority_refs=[
                "blocked-state:work-board-no-connector-write",
                "blocked-state:work-board-no-background-autonomy",
            ],
        ),
        WorkBoardColumnReadModel(
            column_ref="work-board-column:done",
            label="Done",
            status="done",
            safe_summary="Completed or acceptance-baselined lanes with safe proof refs.",
            card_refs=["work-board-card:coding-cockpit-shell"],
            wip_limit=8,
            blocked_authority_refs=[],
        ),
    ]
    cards = [
        _card(
            "work-board-card:setup-assistant-hardening",
            "Setup Assistant hardening",
            "work-board-column:triage",
            "Make first-run local setup clearer without installer side effects or distribution claims.",
            "high",
            "proposal_only",
            "Queued",
            ["route-ref:control-center-setup"],
            ["proof-ref:setup-assistant-read-model"],
            [],
            ["setup", "local-first"],
        ),
        _card(
            "work-board-card:action-inbox-work-queue",
            "Action Inbox work queue",
            "work-board-column:ready",
            "Show exact local work, approval posture, blocked states, receipts, and proof refs.",
            "critical",
            "enabled_read_only",
            "Ready",
            ["route-ref:control-center-actions"],
            ["proof-ref:action-inbox-queue"],
            [],
            ["actions", "approvals"],
        ),
        _card(
            "work-board-card:proof-run-spine",
            "Universal Proof spine",
            "work-board-column:ready",
            "Bind actions, evidence, receipts, memory, and setup events into coherent proof detail.",
            "critical",
            "enabled_read_only",
            "Ready",
            ["route-ref:control-center-proof"],
            ["proof-ref:universal-proof-spine"],
            [],
            ["proof", "receipts"],
        ),
        _card(
            "work-board-card:work-board-kanban-shell",
            "Kanban Work Board shell",
            "work-board-column:doing",
            "Render the Work Board as a real cockpit from Python Core read-model truth.",
            "critical",
            "enabled_read_only",
            "In progress",
            [WORK_BOARD_ROUTE_REF],
            ["proof-ref:work-board-kanban-shell"],
            [],
            ["kanban", "control-center"],
        ),
        _card(
            "work-board-card:daily-loop-productization",
            "Daily loop productization",
            "work-board-column:doing",
            "Unify Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and Settings.",
            "high",
            "enabled_read_only",
            "Hardening",
            ["route-ref:control-center-today"],
            ["proof-ref:daily-loop-productization"],
            [],
            ["today", "loop"],
        ),
        _card(
            "work-board-card:trust-authority-map",
            "Trust authority map",
            "work-board-column:review",
            "Keep enabled, review-only, planned, blocked, safe-disable, rollback, and CLI inspection visible.",
            "high",
            "enabled_read_only",
            "Review",
            ["route-ref:control-center-trust"],
            ["proof-ref:trust-authority-map"],
            [],
            ["trust", "authority"],
        ),
        _card(
            WORK_BOARD_SOCIAL_CONTENT_CARD_REF,
            "Social read-only foundation",
            "work-board-column:review",
            "Track the Q25 owner-foundation acceptance work without copying task lifecycle or granting social publishing authority.",
            "high",
            "proposal_only",
            "Foundation review",
            [
                WORK_BOARD_ROUTE_REF,
                "route-ref:control-center-communications",
                "route-ref:control-center-crm",
            ],
            ["proof-ref:q25-social-read-only-foundation"],
            ["blocked-state:q25-social-foundation-acceptance-incomplete"],
            [WORK_BOARD_SOCIAL_CONTENT_FILTER_TAG, "q25", "cross-app"],
        ),
        _card(
            "work-board-card:external-agent-dispatch",
            "External agent dispatch",
            "work-board-column:blocked",
            "Full-strength multi-agent orchestration requires implemented provider and local-agent AuthorityLease scopes, exact approval, receipts, and safe-disable posture.",
            "medium",
            "blocked",
            "Blocked",
            ["route-ref:control-center-coding"],
            ["proof-ref:multi-agent-blocked"],
            [
                "blocked-state:work-board-no-background-autonomy",
                "blocked-state:work-board-no-production-authority",
            ],
            ["agents", "blocked"],
        ),
        _card(
            "work-board-card:connector-write-actions",
            "Connector write actions",
            "work-board-column:blocked",
            "Email, calendar, CRM, and external connector writes remain draft-only until exact approval lanes exist.",
            "medium",
            "blocked",
            "Blocked",
            ["route-ref:control-center-sources"],
            ["proof-ref:connector-write-blocked"],
            ["blocked-state:work-board-no-connector-write"],
            ["connectors", "blocked"],
        ),
        _card(
            "work-board-card:coding-cockpit-shell",
            "Coding Cockpit shell",
            "work-board-column:done",
            "Read-only Coding cockpit baseline with context, patch, terminal, Git, preview, and agent review posture.",
            "high",
            "enabled_read_only",
            "Merged",
            ["route-ref:control-center-coding"],
            ["proof-ref:coding-cockpit-shell"],
            [],
            ["coding", "cockpit"],
        ),
    ]
    return columns, cards


def build_work_board_read_model(
    *,
    apply_persisted_state: bool = True,
    store: WorkBoardStateStore | None = None,
) -> WorkBoardReadModel:
    columns, cards = _base_work_board()
    latest_reorder_receipt = None
    latest_card_create_receipt = None
    latest_task_create_receipt = None
    local_task_records: list[WorkBoardLocalTaskReadModel] = []
    if apply_persisted_state:
        active_store = store or WorkBoardStateStore()
        try:
            local_cards = active_store.load_local_cards()
            if local_cards:
                cards = [*cards, *local_cards]
            local_task_records = active_store.load_local_task_records()
            layout = active_store.load_layout()
            if layout is not None:
                _validate_layout_against_board(layout, columns=columns, cards=cards)
                latest_reorder_receipt = active_store.latest_receipt()
                latest_card_create_receipt = active_store.latest_card_create_receipt()
                latest_task_create_receipt = active_store.latest_task_create_receipt()
                columns, cards = _apply_layout(
                    columns=columns,
                    cards=cards,
                    layout=layout,
                )
        except (OSError, ValueError, json.JSONDecodeError, WorkBoardStorageError):
            latest_reorder_receipt = None
            latest_card_create_receipt = None
            latest_task_create_receipt = None
            local_task_records = []
    return WorkBoardReadModel(
        title="Work Board",
        safe_summary=(
            "Backend-owned Kanban read model for the Founder Command Center. "
            "Control Center may filter, select, preview drag/drop order locally, "
            "persist exact approved reorder receipts, create exact approved local "
            "cards, and create exact approved local task records through Python Core."
        ),
        repo_safe_scope=(
            "Render a polished Kanban cockpit, safe refs, exact approved reorder "
            "local-card-create, and local-task-record persistence, blocked external authority, and "
            "receipt posture. No issue tracker, connector, shell, browser, or "
            "background work is invoked."
        ),
        full_strength_goal=(
            "A real operator Work Board where plans, actions, receipts, proof, "
            "agents, Git, and releases eventually coordinate through exact approval "
            "lanes and reversible receipts."
        ),
        columns=columns,
        cards=cards,
        saved_projections=[
            WorkBoardSavedProjectionReadModel(
                projection_ref=WORK_BOARD_SOCIAL_CONTENT_PROJECTION_REF,
                contract_ref=WORK_BOARD_SOCIAL_CONTENT_PROJECTION_CONTRACT_REF,
                label="Social Content",
                safe_summary=(
                    "Backend-owned saved projection of Work Board cards tagged for "
                    "Q25 Social foundation review. Work Board retains lifecycle and "
                    "ordering ownership."
                ),
                owner_ref="owner-ref:python-agent-core-work-board",
                filter_tags=[WORK_BOARD_SOCIAL_CONTENT_FILTER_TAG],
                link_contract_refs=[
                    "link-contract-ref:social-originating-signal",
                    "link-contract-ref:social-campaign",
                    "link-contract-ref:social-evidence",
                    "link-contract-ref:social-schedule",
                ],
                proof_refs=["proof-ref:q25-work-board-social-content-projection"],
                evidence_refs=["evidence-ref:work-board-read-model"],
                blocker_refs=[
                    "blocked-state:q25-social-foundation-acceptance-incomplete",
                    "blocked-state:q25-no-social-publishing",
                ],
            )
        ],
        local_task_records=local_task_records,
        blocked_lanes=[
            WorkBoardBlockedLaneReadModel(
                lane_ref="blocked-lane:work-board-external-sync",
                label="External sync",
                safe_summary="Issue tracker, connector, and agent dispatch writes are separate authority lanes.",
                blocked_authority_refs=[
                    "blocked-state:work-board-no-issue-tracker-write",
                    "blocked-state:work-board-no-connector-write",
                    "blocked-state:work-board-no-background-autonomy",
                ],
                promotion_path_refs=["prompt-ref:unblock-work-board-external-sync"],
            ),
        ],
        drag_drop_posture=WorkBoardDragDropPostureReadModel(
            safe_summary=(
                "Cards can be dragged or moved by keyboard as a local layout preview. "
                "Persisting the order requires the exact reorder route, idempotency, "
                "safe-disable, rollback posture, and receipt refs."
            ),
            blocked_authority_refs=[
                WORK_BOARD_BLOCKED_CARD_ARCHIVE_ASSIGNMENT_REF,
                "blocked-state:work-board-no-issue-tracker-write",
            ],
            promotion_path_refs=["prompt-ref:work-board-card-mutation-lane"],
        ),
        proof_refs=[
            "proof-ref:work-board-kanban-shell",
            WORK_BOARD_REORDER_PROOF_REF,
            WORK_BOARD_CARD_CREATE_PROOF_REF,
            WORK_BOARD_TASK_CREATE_PROOF_REF,
        ],
        evidence_refs=[
            "evidence-ref:work-board-read-model",
            WORK_BOARD_REORDER_EVIDENCE_REF,
            WORK_BOARD_CARD_CREATE_EVIDENCE_REF,
            WORK_BOARD_TASK_CREATE_EVIDENCE_REF,
        ],
        blocked_authority_refs=WORK_BOARD_REQUIRED_BLOCKED_REFS,
        promotion_path_refs=[
            "prompt-ref:work-board-card-mutation-lane",
            "prompt-ref:unblock-work-board-external-sync",
        ],
        redactions_applied=[
            "redaction-ref:safe-refs-only",
            "redaction-ref:raw-paths-omitted",
            "redaction-ref:raw-content-omitted",
        ],
        next_safe_action=(
            "Use the board for local planning, preview drag/drop, and exact approved "
            "persisted reorder, card create, or local task record create. Promote archive, assignment, and external sync as "
            "separate lanes."
        ),
        latest_reorder_receipt_ref=(
            latest_reorder_receipt.receipt_ref
            if latest_reorder_receipt is not None
            else None
        ),
        latest_card_create_receipt_ref=(
            latest_card_create_receipt.receipt_ref
            if latest_card_create_receipt is not None
            else None
        ),
        latest_task_create_receipt_ref=(
            latest_task_create_receipt.receipt_ref
            if latest_task_create_receipt is not None
            else None
        ),
    )


def _card(
    card_ref: str,
    title: str,
    column_ref: str,
    safe_summary: str,
    priority: CardPriority,
    authority_state: CardAuthorityState,
    progress_label: str,
    surface_refs: list[str],
    proof_refs: list[str],
    blocker_refs: list[str],
    tags: list[str],
) -> WorkBoardCardReadModel:
    return WorkBoardCardReadModel(
        card_ref=card_ref,
        title=title,
        safe_summary=safe_summary,
        column_ref=column_ref,
        priority=priority,
        authority_state=authority_state,
        owner_ref="owner-ref:python-agent-core-work-board",
        progress_label=progress_label,
        proof_refs=proof_refs,
        evidence_refs=["evidence-ref:work-board-read-model"],
        blocker_refs=blocker_refs,
        surface_refs=surface_refs,
        cli_inspection_refs=[WORK_BOARD_CLI_REF],
        tags=tags,
    )
