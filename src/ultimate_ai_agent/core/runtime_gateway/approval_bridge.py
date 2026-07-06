from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
RUNTIME_APPROVAL_BRIDGE_ACTION_INBOX_REF = (
    "action-inbox-ref:runtime-approval-bridge:approval-wait-sample"
)
RUNTIME_APPROVAL_BRIDGE_PROOF_REF = "proof-ref:runtime-approval-bridge:phase-04"


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
    timeout_policy_ref: str = "timeout-policy-ref:runtime-approval-bridge:default-deny"
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


class RuntimeApprovalBridgeReadModel(BaseModel):
    schema_version: str = "runtime_approval_bridge.v1"
    contract_ref: str = RUNTIME_APPROVAL_BRIDGE_CONTRACT_REF
    route_ref: str = RUNTIME_APPROVAL_BRIDGE_ROUTE_REF
    cli_ref: str = RUNTIME_APPROVAL_BRIDGE_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    status: str = "read_model_resolution_blocked"
    action_inbox_projection: RuntimeApprovalActionInboxProjection = Field(
        default_factory=RuntimeApprovalActionInboxProjection
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
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.status, "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
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
    requested_scope_ref = "runtime-approval-scope-ref:hermes-agent:sample"
    envelope_ref = "runtime-approval-envelope-ref:hermes-agent:sample"
    blocked_refs = [
        *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
        "blocked-authority:runtime-approval-resolution-send",
        "blocked-authority:runtime-approval-approval-as-authority",
        "blocked-authority:runtime-approval-timeout-send",
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
            receipt_ref="receipt-plan-ref:runtime-approval-bridge:timeout-deny",
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
    return RuntimeApprovalBridgeReadModel(
        envelopes=[envelope],
        decision_previews=decisions,
        scope_validation=validate_runtime_approval_scope(
            requested_scope_ref,
            "runtime-approval-scope-ref:hermes-agent:other",
        ),
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
