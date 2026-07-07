from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)
from ultimate_ai_agent.core.runtime_gateway.run_events import (
    RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
    RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
)


RUNTIME_APPROVAL_BRIDGE_CONTRACT_REF = "contract-ref:runtime-approval-bridge:v1"
RUNTIME_APPROVAL_BRIDGE_ROUTE_REF = "GET /api/runtime/approval-bridge"
RUNTIME_APPROVAL_BRIDGE_CLI_REF = "uaa runtime inspect-approval-bridge"
RUNTIME_APPROVAL_BRIDGE_SNAPSHOT_REF = (
    "runtime-approval-bridge-snapshot-ref:hermes-agent:review-metadata"
)
RUNTIME_APPROVAL_BRIDGE_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_APPROVAL_BRIDGE_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_APPROVAL_BRIDGE_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-approval-bridge-read-model"
)
RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF = (
    "action-inbox-ref:runtime-approval-bridge:approval-wait-sample"
)
RUNTIME_APPROVAL_BRIDGE_PROOF_REF = "proof-ref:runtime-approval-bridge:phase-04"
RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF = (
    "timeout-policy-ref:runtime-approval-bridge:fail-closed-v1"
)
RUNTIME_APPROVAL_TIMEOUT_DENIAL_RECEIPT_REF = (
    "receipt-plan-ref:runtime-approval-bridge:timeout-deny"
)
RUNTIME_APPROVAL_AMBIGUOUS_DENIAL_RECEIPT_REF = (
    "receipt-plan-ref:runtime-approval-bridge:ambiguous-deny"
)
RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:runtime-approval-auto-approve",
    "blocked-authority:runtime-approval-approve-all",
    "blocked-authority:runtime-approval-standing-broad-authority",
    "blocked-authority:runtime-approval-expired-grant-reuse",
    "blocked-authority:runtime-approval-ambiguous-grant",
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}


class RuntimeApprovalBridgeState(str, Enum):
    runtime_requested = "runtime_requested"
    uaa_review_required = "uaa_review_required"
    uaa_denial_preview = "uaa_denial_preview"
    timeout_blocked = "timeout_blocked"
    scope_mismatch_blocked = "scope_mismatch_blocked"
    resolution_blocked = "resolution_blocked"


class RuntimeApprovalBridgeDecisionKind(str, Enum):
    approve = "approve"
    deny = "deny"
    timeout = "timeout"
    scope_mismatch = "scope_mismatch"


class RuntimeApprovalBridgeResolutionPosture(str, Enum):
    local_review_only = "local_review_only"
    blocked_no_runtime_send = "blocked_no_runtime_send"
    approval_required_future_lane = "approval_required_future_lane"


class RuntimeApprovalScopeValidationResult(BaseModel):
    validation_ref: str
    requested_scope_ref: str
    provided_scope_ref: str
    scope_matches: bool
    status: str
    safe_summary: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_result(self) -> "RuntimeApprovalScopeValidationResult":
        for value, field_name in [
            (self.validation_ref, "validation_ref"),
            (self.requested_scope_ref, "requested_scope_ref"),
            (self.provided_scope_ref, "provided_scope_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.status, "status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.scope_matches and self.status != "scope_match_review_only":
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SCOPE_STATUS_DRIFT")
        if not self.scope_matches and self.status != "scope_mismatch_blocked":
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SCOPE_MISMATCH_REQUIRED")
        return self


class RuntimeApprovalBridgeEnvelope(BaseModel):
    envelope_ref: str
    runtime_approval_ref: str
    runtime_run_ref: str
    uaa_durable_run_ref: str
    action_inbox_item_ref: str
    proof_ref: str
    requested_scope_ref: str
    idempotency_key_ref: str
    side_effect_class: str = "runtime_approval_resolution"
    risk_class: str = "medium"
    state: RuntimeApprovalBridgeState
    resolution_posture: RuntimeApprovalBridgeResolutionPosture = (
        RuntimeApprovalBridgeResolutionPosture.blocked_no_runtime_send
    )
    timeout_policy_ref: str = RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF
    deny_receipt_ref: str = "receipt-plan-ref:runtime-approval-bridge:deny"
    approval_refs_are_identifiers_only: bool = True
    runtime_requested: bool = True
    uaa_approval_recorded: bool = False
    runtime_resolution_sent: bool = False
    approval_resolution_enabled: bool = False
    denial_resolution_enabled: bool = False
    timeout_defaults_to_deny: bool = True
    raw_runtime_payload_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_envelope(self) -> "RuntimeApprovalBridgeEnvelope":
        for value, field_name in [
            (self.envelope_ref, "envelope_ref"),
            (self.runtime_approval_ref, "runtime_approval_ref"),
            (self.runtime_run_ref, "runtime_run_ref"),
            (self.uaa_durable_run_ref, "uaa_durable_run_ref"),
            (self.action_inbox_item_ref, "action_inbox_item_ref"),
            (self.proof_ref, "proof_ref"),
            (self.requested_scope_ref, "requested_scope_ref"),
            (self.idempotency_key_ref, "idempotency_key_ref"),
            (self.timeout_policy_ref, "timeout_policy_ref"),
            (self.deny_receipt_ref, "deny_receipt_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.side_effect_class, "side_effect_class"),
            (self.risk_class, "risk_class"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in ("blocked_authority_refs", "next_safe_action_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        denied_flags = {
            "runtime_resolution_sent": self.runtime_resolution_sent,
            "approval_resolution_enabled": self.approval_resolution_enabled,
            "denial_resolution_enabled": self.denial_resolution_enabled,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_APPROVAL_BRIDGE_RESOLUTION_DENIED: " + ", ".join(enabled)
            )
        if not self.approval_refs_are_identifiers_only:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_APPROVAL_REF_AUTHORITY_DENIED")
        if not self.timeout_defaults_to_deny:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_TIMEOUT_DENY_REQUIRED")
        return self


class RuntimeApprovalBridgeDecisionPreview(BaseModel):
    decision_ref: str
    decision_kind: RuntimeApprovalBridgeDecisionKind
    envelope_ref: str
    action_inbox_item_ref: str
    receipt_ref: str
    runtime_resolution_sent: bool = False
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> "RuntimeApprovalBridgeDecisionPreview":
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.envelope_ref, "envelope_ref"),
            (self.action_inbox_item_ref, "action_inbox_item_ref"),
            (self.receipt_ref, "receipt_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_refs")
        if self.runtime_resolution_sent:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_DECISION_SEND_DENIED")
        return self


class RuntimeApprovalActionInboxProjection(BaseModel):
    action_inbox_item_ref: str = RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF
    source: str = "runtime_approval_bridge_read_model"
    lane: str = "runtime_approval_review"
    status: str = "review_required_resolution_blocked"
    proof_ref: str = RUNTIME_APPROVAL_BRIDGE_PROOF_REF
    approval_controls_visible: bool = False
    runtime_resolution_controls_visible: bool = False
    safe_summary: str = (
        "Runtime approval waits can appear as Action Inbox review metadata, "
        "but this lane cannot resolve the runtime wait."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_projection(self) -> "RuntimeApprovalActionInboxProjection":
        for value, field_name in [
            (self.action_inbox_item_ref, "action_inbox_item_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.source, "source"),
            (self.lane, "lane"),
            (self.status, "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.approval_controls_visible or self.runtime_resolution_controls_visible:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_UI_CONTROL_DENIED")
        return self


class RuntimeApprovalFailClosedTimeoutPosture(BaseModel):
    policy_ref: str = RUNTIME_APPROVAL_FAIL_CLOSED_POLICY_REF
    status: str = "fail_closed_default_deny"
    timeout_denial_receipt_ref: str = RUNTIME_APPROVAL_TIMEOUT_DENIAL_RECEIPT_REF
    ambiguous_denial_receipt_ref: str = RUNTIME_APPROVAL_AMBIGUOUS_DENIAL_RECEIPT_REF
    expired_waits_default_to_deny: bool = True
    ambiguous_waits_default_to_deny: bool = True
    explicit_expiration_required: bool = True
    revoke_required: bool = True
    safe_disable_required: bool = True
    auto_approve_enabled: bool = False
    approve_all_enabled: bool = False
    standing_broad_authority_enabled: bool = False
    expired_grant_reuse_enabled: bool = False
    ambiguous_grant_enabled: bool = False
    approval_resolution_sent: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS)
    )
    promotion_path_refs: list[str] = Field(
        default_factory=lambda: [
            "promotion-path-ref:runtime-approval:session-scoped-grant",
            "promotion-path-ref:runtime-approval:explicit-expiration",
            "promotion-path-ref:runtime-approval:receipt-and-revoke",
            "promotion-path-ref:runtime-approval:safe-disable",
        ]
    )
    next_safe_action_refs: list[str] = Field(
        default_factory=lambda: [
            "next-safe-action-ref:runtime-approval:record-timeout-denial-receipt",
            "next-safe-action-ref:runtime-approval:prove-ambiguous-wait-denial",
            "next-safe-action-ref:runtime-approval:bind-explicit-revoke",
        ]
    )
    safe_summary: str = (
        "Expired or ambiguous approval waits deny by default; approve-all and "
        "standing authority remain blocked."
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "RuntimeApprovalFailClosedTimeoutPosture":
        for value, field_name in [
            (self.policy_ref, "policy_ref"),
            (self.timeout_denial_receipt_ref, "timeout_denial_receipt_ref"),
            (self.ambiguous_denial_receipt_ref, "ambiguous_denial_receipt_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.status, "status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        required_true = {
            "expired_waits_default_to_deny": self.expired_waits_default_to_deny,
            "ambiguous_waits_default_to_deny": self.ambiguous_waits_default_to_deny,
            "explicit_expiration_required": self.explicit_expiration_required,
            "revoke_required": self.revoke_required,
            "safe_disable_required": self.safe_disable_required,
        }
        missing = [name for name, value in required_true.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_APPROVAL_FAIL_CLOSED_REQUIRED: " + ", ".join(missing)
            )
        denied_flags = {
            "auto_approve_enabled": self.auto_approve_enabled,
            "approve_all_enabled": self.approve_all_enabled,
            "standing_broad_authority_enabled": self.standing_broad_authority_enabled,
            "expired_grant_reuse_enabled": self.expired_grant_reuse_enabled,
            "ambiguous_grant_enabled": self.ambiguous_grant_enabled,
            "approval_resolution_sent": self.approval_resolution_sent,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_APPROVAL_FAIL_CLOSED_UNSAFE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        for ref in RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKER_MISSING")
        return self


class RuntimeApprovalBridgeReadModel(BaseModel):
    schema_version: str = "runtime_approval_bridge.v1"
    contract_ref: str = RUNTIME_APPROVAL_BRIDGE_CONTRACT_REF
    snapshot_ref: str = RUNTIME_APPROVAL_BRIDGE_SNAPSHOT_REF
    snapshot_hash_ref: str
    route_ref: str = RUNTIME_APPROVAL_BRIDGE_ROUTE_REF
    cli_ref: str = RUNTIME_APPROVAL_BRIDGE_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    status: str = "read_model_resolution_blocked"
    authority_state_route_ref: str
    authority_state_cli_ref: str
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    action_inbox_projection: RuntimeApprovalActionInboxProjection = Field(
        default_factory=RuntimeApprovalActionInboxProjection
    )
    fail_closed_timeout_posture: RuntimeApprovalFailClosedTimeoutPosture = Field(
        default_factory=RuntimeApprovalFailClosedTimeoutPosture
    )
    envelopes: list[RuntimeApprovalBridgeEnvelope]
    decision_previews: list[RuntimeApprovalBridgeDecisionPreview]
    scope_validation: RuntimeApprovalScopeValidationResult
    pending_runtime_approval_count: int
    denied_preview_count: int
    timeout_preview_count: int
    scope_mismatch_count: int
    runtime_resolution_sent_count: int = 0
    approval_resolution_route_enabled: bool = False
    deny_resolution_route_enabled: bool = False
    timeout_resolution_route_enabled: bool = False
    uaa_controls_authority: bool = True
    control_center_talks_directly_to_runtime: bool = False
    safe_refs_only: bool = True
    raw_runtime_payload_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Runtime approval waits are projected into UAA review metadata only; "
        "approval, denial, timeout, and scope mismatch outcomes are not sent to the runtime."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + ["runtime_approval_payload_omitted"]
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeApprovalBridgeReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.status, "status"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_APPROVAL_BRIDGE_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_AUTHORITY_DECISION_INVALID")
        if self.pending_runtime_approval_count != sum(
            1 for envelope in self.envelopes if envelope.state == "runtime_requested"
        ):
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_PENDING_COUNT_DRIFT")
        if self.denied_preview_count != sum(
            1
            for preview in self.decision_previews
            if preview.decision_kind == "deny"
        ):
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_DENIAL_COUNT_DRIFT")
        if self.timeout_preview_count != sum(
            1
            for preview in self.decision_previews
            if preview.decision_kind == "timeout"
        ):
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_TIMEOUT_COUNT_DRIFT")
        if self.scope_mismatch_count != sum(
            1
            for preview in self.decision_previews
            if preview.decision_kind == "scope_mismatch"
        ):
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SCOPE_MISMATCH_COUNT_DRIFT")
        if self.scope_validation.scope_matches and self.scope_mismatch_count != 0:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SCOPE_VALIDATION_DRIFT")
        if not self.scope_validation.scope_matches and self.scope_mismatch_count == 0:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SCOPE_MISMATCH_REQUIRED")
        if self.runtime_resolution_sent_count != 0:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_RUNTIME_SEND_DENIED")
        denied_flags = {
            "approval_resolution_route_enabled": self.approval_resolution_route_enabled,
            "deny_resolution_route_enabled": self.deny_resolution_route_enabled,
            "timeout_resolution_route_enabled": self.timeout_resolution_route_enabled,
            "control_center_talks_directly_to_runtime": (
                self.control_center_talks_directly_to_runtime
            ),
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_APPROVAL_BRIDGE_UNSAFE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.uaa_controls_authority:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_UAA_AUTHORITY_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_APPROVAL_BRIDGE_SAFE_REFS_REQUIRED")
        for ref in self.fail_closed_timeout_posture.blocked_authority_refs:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_APPROVAL_BRIDGE_FAIL_CLOSED_BLOCKER_DRIFT")
        return self


def validate_runtime_approval_scope(
    requested_scope_ref: str,
    provided_scope_ref: str,
) -> RuntimeApprovalScopeValidationResult:
    matches = requested_scope_ref == provided_scope_ref
    return RuntimeApprovalScopeValidationResult(
        validation_ref="validation-ref:runtime-approval-bridge:scope",
        requested_scope_ref=requested_scope_ref,
        provided_scope_ref=provided_scope_ref,
        scope_matches=matches,
        status="scope_match_review_only" if matches else "scope_mismatch_blocked",
        safe_summary=(
            "Runtime approval scope matched; review remains local only."
            if matches
            else "Runtime approval scope mismatch blocks any future resolution."
        ),
    )


def build_runtime_approval_bridge_read_model() -> RuntimeApprovalBridgeReadModel:
    authority_entry = _authority_entry(authority_decision_catalog=None)
    return build_runtime_approval_bridge_read_model_from_authority_catalog(
        authority_decision_catalog=[authority_entry]
    )


def build_runtime_approval_bridge_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeApprovalBridgeReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    requested_scope_ref = "runtime-approval-scope-ref:hermes-agent:sample"
    envelope_ref = "runtime-approval-envelope-ref:hermes-agent:sample"
    blocked_refs = [
        *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
        "blocked-authority:runtime-approval-resolution-send",
        "blocked-authority:runtime-approval-approval-as-authority",
        "blocked-authority:runtime-approval-timeout-send",
        *RUNTIME_APPROVAL_FAIL_CLOSED_BLOCKED_AUTHORITY_REFS,
    ]
    envelope = RuntimeApprovalBridgeEnvelope(
        envelope_ref=envelope_ref,
        runtime_approval_ref="runtime-approval-ref:hermes-agent:sample",
        runtime_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_RUN_REF,
        uaa_durable_run_ref=RUNTIME_RUN_EVENTS_SAMPLE_DURABLE_RUN_REF,
        action_inbox_item_ref=RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF,
        proof_ref=RUNTIME_APPROVAL_BRIDGE_PROOF_REF,
        requested_scope_ref=requested_scope_ref,
        idempotency_key_ref="idempotency-ref:runtime-approval-bridge:sample",
        state=RuntimeApprovalBridgeState.runtime_requested,
        safe_summary=(
            "Hermes runtime requested approval; UAA records only a review envelope "
            "and does not send a resolution."
        ),
        blocked_authority_refs=blocked_refs,
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-approval-bridge:bind-local-approval-authority",
            "next-safe-action-ref:runtime-approval-bridge:add-denial-receipt",
            "next-safe-action-ref:runtime-approval-bridge:prove-timeout-default-deny",
        ],
    )
    decisions = [
        RuntimeApprovalBridgeDecisionPreview(
            decision_ref="decision-ref:runtime-approval-bridge:deny-preview",
            decision_kind=RuntimeApprovalBridgeDecisionKind.deny,
            envelope_ref=envelope_ref,
            action_inbox_item_ref=RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF,
            receipt_ref="receipt-plan-ref:runtime-approval-bridge:deny",
            safe_summary=(
                "Denial can be represented as a local receipt plan but is not sent "
                "to the runtime in Phase 04."
            ),
            blocked_authority_refs=blocked_refs,
        ),
        RuntimeApprovalBridgeDecisionPreview(
            decision_ref="decision-ref:runtime-approval-bridge:timeout-preview",
            decision_kind=RuntimeApprovalBridgeDecisionKind.timeout,
            envelope_ref=envelope_ref,
            action_inbox_item_ref=RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF,
            receipt_ref=RUNTIME_APPROVAL_TIMEOUT_DENIAL_RECEIPT_REF,
            safe_summary=(
                "Timeout defaults to deny posture locally; runtime send remains blocked."
            ),
            blocked_authority_refs=blocked_refs,
        ),
        RuntimeApprovalBridgeDecisionPreview(
            decision_ref="decision-ref:runtime-approval-bridge:scope-mismatch-preview",
            decision_kind=RuntimeApprovalBridgeDecisionKind.scope_mismatch,
            envelope_ref=envelope_ref,
            action_inbox_item_ref=RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF,
            receipt_ref="receipt-plan-ref:runtime-approval-bridge:scope-mismatch",
            safe_summary=(
                "Scope mismatch blocks any future approval resolution attempt."
            ),
            blocked_authority_refs=blocked_refs,
        ),
    ]
    scope_validation = validate_runtime_approval_scope(
        requested_scope_ref,
        "runtime-approval-scope-ref:hermes-agent:other",
    )
    fail_closed_timeout_posture = RuntimeApprovalFailClosedTimeoutPosture()
    return RuntimeApprovalBridgeReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(
            action_inbox_projection=RuntimeApprovalActionInboxProjection(),
            fail_closed_timeout_posture=fail_closed_timeout_posture,
            envelopes=[envelope],
            decision_previews=decisions,
            scope_validation=scope_validation,
            authority_entry=authority_entry,
        ),
        authority_state_route_ref=RUNTIME_APPROVAL_BRIDGE_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_APPROVAL_BRIDGE_AUTHORITY_STATE_CLI_REF,
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        fail_closed_timeout_posture=fail_closed_timeout_posture,
        envelopes=[envelope],
        decision_previews=decisions,
        scope_validation=scope_validation,
        pending_runtime_approval_count=1,
        denied_preview_count=1,
        timeout_preview_count=1,
        scope_mismatch_count=1,
        blocked_authority_refs=blocked_refs,
        proof_refs=[
            RUNTIME_APPROVAL_BRIDGE_PROOF_REF,
            "proof-ref:runtime-approval-bridge:action-inbox-projection",
            "proof-ref:runtime-approval-bridge:timeout-default-deny",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-approval-bridge:validate-exact-scope",
            "next-safe-action-ref:runtime-approval-bridge:bind-idempotency",
            "next-safe-action-ref:runtime-approval-bridge:add-runtime-resolution-receipt",
        ],
    )


def _snapshot_hash_ref(
    *,
    action_inbox_projection: RuntimeApprovalActionInboxProjection,
    fail_closed_timeout_posture: RuntimeApprovalFailClosedTimeoutPosture,
    envelopes: list[RuntimeApprovalBridgeEnvelope],
    decision_previews: list[RuntimeApprovalBridgeDecisionPreview],
    scope_validation: RuntimeApprovalScopeValidationResult,
    authority_entry: AuthorityDecisionCatalogEntry,
) -> str:
    payload = {
        "contract_ref": RUNTIME_APPROVAL_BRIDGE_CONTRACT_REF,
        "snapshot_ref": RUNTIME_APPROVAL_BRIDGE_SNAPSHOT_REF,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "action_inbox_projection": action_inbox_projection.model_dump(mode="json"),
        "fail_closed_timeout_posture": fail_closed_timeout_posture.model_dump(
            mode="json"
        ),
        "envelopes": [envelope.model_dump(mode="json") for envelope in envelopes],
        "decision_previews": [
            preview.model_dump(mode="json") for preview in decision_previews
        ],
        "scope_validation": scope_validation.model_dump(mode="json"),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-approval-bridge:{digest[:16]}"


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_APPROVAL_BRIDGE_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_APPROVAL_BRIDGE_AUTHORITY_MAPPING_MISSING")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
