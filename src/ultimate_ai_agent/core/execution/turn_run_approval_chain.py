from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    validate_execution_ref,
    validate_safe_execution_text,
)


TURN_RUN_APPROVAL_CHAIN_SCHEMA_VERSION = "turn_run_approval_chain.v1"
TURN_RUN_APPROVAL_CHAIN_CONTRACT_REF = "contract-ref:turn-run-approval-chain:v1"
TURN_RUN_APPROVAL_CHAIN_CLI_REF = "repo-local-command:uaa-runtime-inspect-turn-run-approval-chain"
TURN_RUN_APPROVAL_CHAIN_API_READ_MODEL_REF = "api-read-model:turn-run-approval-chain"
TURN_RUN_APPROVAL_CHAIN_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:turn-run-chain-no-approval-as-execution",
    "blocked-authority:turn-run-chain-no-background-autonomy",
    "blocked-authority:turn-run-chain-no-provider-model-call",
    "blocked-authority:turn-run-chain-no-tool-execution",
    "blocked-authority:turn-run-chain-no-shell-subprocess",
    "blocked-authority:turn-run-chain-no-browser-automation",
    "blocked-authority:turn-run-chain-no-connector-write",
    "blocked-authority:turn-run-chain-no-production-authority",
)


class TurnRunApprovalState(str, Enum):
    created = "created"
    routed = "routed"
    planning = "planning"
    waiting_for_approval = "waiting_for_approval"
    approved = "approved"
    running = "running"
    retry_scheduled = "retry_scheduled"
    paused = "paused"
    resumed = "resumed"
    cancelled = "cancelled"
    failed = "failed"
    blocked = "blocked"
    completed = "completed"


class TurnRunApprovalTransitionStatus(str, Enum):
    accepted = "accepted"
    denied = "denied"
    idempotent_replay = "idempotent_replay"


TURN_RUN_APPROVAL_CANONICAL_STATES = tuple(item.value for item in TurnRunApprovalState)
TURN_RUN_APPROVAL_TERMINAL_STATES = {
    TurnRunApprovalState.cancelled,
    TurnRunApprovalState.completed,
}
TURN_RUN_APPROVAL_ALLOWED_TRANSITIONS: dict[TurnRunApprovalState, set[TurnRunApprovalState]] = {
    TurnRunApprovalState.created: {TurnRunApprovalState.routed, TurnRunApprovalState.blocked, TurnRunApprovalState.cancelled},
    TurnRunApprovalState.routed: {TurnRunApprovalState.planning, TurnRunApprovalState.blocked, TurnRunApprovalState.cancelled},
    TurnRunApprovalState.planning: {
        TurnRunApprovalState.waiting_for_approval,
        TurnRunApprovalState.running,
        TurnRunApprovalState.blocked,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.waiting_for_approval: {
        TurnRunApprovalState.approved,
        TurnRunApprovalState.blocked,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.approved: {TurnRunApprovalState.running, TurnRunApprovalState.blocked, TurnRunApprovalState.cancelled},
    TurnRunApprovalState.running: {
        TurnRunApprovalState.paused,
        TurnRunApprovalState.retry_scheduled,
        TurnRunApprovalState.failed,
        TurnRunApprovalState.blocked,
        TurnRunApprovalState.completed,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.retry_scheduled: {
        TurnRunApprovalState.running,
        TurnRunApprovalState.blocked,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.paused: {
        TurnRunApprovalState.resumed,
        TurnRunApprovalState.failed,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.resumed: {
        TurnRunApprovalState.running,
        TurnRunApprovalState.blocked,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.failed: {TurnRunApprovalState.retry_scheduled, TurnRunApprovalState.cancelled},
    TurnRunApprovalState.blocked: {
        TurnRunApprovalState.retry_scheduled,
        TurnRunApprovalState.failed,
        TurnRunApprovalState.cancelled,
    },
    TurnRunApprovalState.cancelled: set(),
    TurnRunApprovalState.completed: set(),
}


class TurnRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "TurnRef":
        validate_execution_ref(self.ref, "turn_ref")
        return self


class DurableRunRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "DurableRunRef":
        validate_execution_ref(self.ref, "durable_run_ref")
        return self


class ApprovalRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "ApprovalRef":
        validate_execution_ref(self.ref, "approval_ref")
        return self


class CheckpointRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "CheckpointRef":
        validate_execution_ref(self.ref, "checkpoint_ref")
        return self


class ReceiptRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "ReceiptRef":
        validate_execution_ref(self.ref, "receipt_ref")
        return self


class RouteDecisionBindingRef(BaseModel):
    ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_ref(self) -> "RouteDecisionBindingRef":
        validate_execution_ref(self.ref, "route_decision_binding_ref")
        return self


class TurnRunApprovalLinkage(BaseModel):
    turn_ref: TurnRef | None = None
    durable_run_ref: DurableRunRef
    operator_task_ref: str | None = None
    approval_ref: ApprovalRef | None = None
    route_decision_binding_ref: RouteDecisionBindingRef | None = None
    checkpoint_refs: list[CheckpointRef] = Field(default_factory=list)
    receipt_refs: list[ReceiptRef] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_linkage(self) -> "TurnRunApprovalLinkage":
        if self.turn_ref is None and self.operator_task_ref is None:
            raise ValueError("turn/run approval linkage requires a safe turn ref or operator task ref")
        if self.operator_task_ref is not None:
            validate_execution_ref(self.operator_task_ref, "operator_task_ref")
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "linkage_evidence_ref")
        if not self.safe_refs_only:
            raise ValueError("turn/run approval linkage must be safe-ref only")
        return self


class TurnRunApprovalIdempotencyRecord(BaseModel):
    idempotency_key: str = Field(..., min_length=1)
    request_fingerprint_ref: str = Field(..., min_length=1)
    transition_ref: str = Field(..., min_length=1)
    accepted_state_before: TurnRunApprovalState
    accepted_state_after: TurnRunApprovalState
    receipt_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "TurnRunApprovalIdempotencyRecord":
        for value, field_name in (
            (self.idempotency_key, "idempotency_key"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.transition_ref, "transition_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.replay_ref, "replay_ref"),
        ):
            validate_execution_ref(value, field_name)
        return self


class TurnRunApprovalTransition(BaseModel):
    transition_ref: str = Field(..., min_length=1)
    from_state: TurnRunApprovalState
    to_state: TurnRunApprovalState
    actor_ref: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)
    checkpoint_ref: CheckpointRef | None = None
    receipt_ref: ReceiptRef
    replay_ref: str = Field(..., min_length=1)
    approval_ref: ApprovalRef | None = None
    route_decision_binding_ref: RouteDecisionBindingRef | None = None
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    append_only_event: bool = True
    replayable: bool = True
    raw_payloads_persisted: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_transition(self) -> "TurnRunApprovalTransition":
        for value, field_name in (
            (self.transition_ref, "transition_ref"),
            (self.actor_ref, "actor_ref"),
            (self.idempotency_key, "idempotency_key"),
            (self.replay_ref, "replay_ref"),
        ):
            validate_execution_ref(value, field_name)
        for ref in [*self.evidence_refs, *self.reason_refs]:
            validate_execution_ref(ref, "turn_run_approval_transition_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.append_only_event or not self.replayable:
            raise ValueError("turn/run approval transitions must be append-only and replayable")
        if self.raw_payloads_persisted or self.execution_performed:
            raise ValueError("turn/run approval transition must not persist raw payloads or execute")
        return self


class TurnRunApprovalTransitionRequest(BaseModel):
    transition_ref: str = Field(..., min_length=1)
    from_state: TurnRunApprovalState
    to_state: TurnRunApprovalState
    actor_ref: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=1)
    checkpoint_ref: str | None = None
    receipt_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    approval_ref: str | None = None
    approval_scope_run_ref: str | None = None
    approval_scope_turn_ref: str | None = None
    route_decision_binding_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    execution_requested: bool = False
    background_autonomy_requested: bool = False
    raw_payloads_included: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "TurnRunApprovalTransitionRequest":
        for value, field_name in (
            (self.transition_ref, "transition_ref"),
            (self.actor_ref, "actor_ref"),
            (self.idempotency_key, "idempotency_key"),
            (self.receipt_ref, "receipt_ref"),
            (self.replay_ref, "replay_ref"),
        ):
            validate_execution_ref(value, field_name)
        for field_name in (
            "checkpoint_ref",
            "approval_ref",
            "approval_scope_run_ref",
            "approval_scope_turn_ref",
            "route_decision_binding_ref",
        ):
            _validate_optional_ref(getattr(self, field_name), field_name)
        for ref in [*self.evidence_refs, *self.reason_refs]:
            validate_execution_ref(ref, "turn_run_approval_request_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        return self


class TurnRunApprovalTransitionDecision(BaseModel):
    decision_ref: str = Field(..., min_length=1)
    status: TurnRunApprovalTransitionStatus
    previous_state: TurnRunApprovalState
    next_state: TurnRunApprovalState
    reason_refs: list[str] = Field(default_factory=list, min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    request_fingerprint_ref: str = Field(..., min_length=1)
    receipt_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    approval_ref_grants_authority: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> "TurnRunApprovalTransitionDecision":
        for value, field_name in (
            (self.decision_ref, "decision_ref"),
            (self.request_fingerprint_ref, "request_fingerprint_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.replay_ref, "replay_ref"),
        ):
            validate_execution_ref(value, field_name)
        for ref in self.reason_refs:
            validate_execution_ref(ref, "transition_decision_reason_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.approval_ref_grants_authority or self.execution_authorized or self.execution_performed:
            raise ValueError("turn/run approval decision cannot grant authority or execute")
        return self


class TurnRunApprovalRetryRecoveryPosture(BaseModel):
    retry_state: str = "inspectable_retry_refs_only"
    recovery_state: str = "inspectable_recovery_refs_only"
    retry_refs: list[str] = Field(default_factory=list)
    recovery_refs: list[str] = Field(default_factory=list)
    retry_execution_enabled: bool = False
    recovery_execution_enabled: bool = False
    background_autonomy_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "TurnRunApprovalRetryRecoveryPosture":
        validate_safe_execution_text(self.retry_state, "retry_state")
        validate_safe_execution_text(self.recovery_state, "recovery_state")
        for ref in [*self.retry_refs, *self.recovery_refs]:
            validate_execution_ref(ref, "retry_recovery_ref")
        if self.retry_execution_enabled or self.recovery_execution_enabled or self.background_autonomy_enabled:
            raise ValueError("turn/run approval retry recovery posture is inspectable only")
        return self


class TurnRunApprovalChainReadModel(BaseModel):
    schema_version: str = TURN_RUN_APPROVAL_CHAIN_SCHEMA_VERSION
    contract_ref: str = TURN_RUN_APPROVAL_CHAIN_CONTRACT_REF
    chain_ref: str = Field(..., min_length=1)
    current_state: TurnRunApprovalState
    linkage: TurnRunApprovalLinkage
    transitions: list[TurnRunApprovalTransition] = Field(default_factory=list)
    idempotency_records: list[TurnRunApprovalIdempotencyRecord] = Field(default_factory=list)
    canonical_states: list[str] = Field(default_factory=lambda: list(TURN_RUN_APPROVAL_CANONICAL_STATES))
    retry_recovery_posture: TurnRunApprovalRetryRecoveryPosture = Field(
        default_factory=TurnRunApprovalRetryRecoveryPosture
    )
    cli_ref: str = TURN_RUN_APPROVAL_CHAIN_CLI_REF
    api_read_model_ref: str = TURN_RUN_APPROVAL_CHAIN_API_READ_MODEL_REF
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_RUN_APPROVAL_CHAIN_BLOCKED_AUTHORITY_REFS)
    )
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    approval_ref_grants_authority: bool = False
    execution_enabled: bool = False
    execution_performed: bool = False
    background_autonomy_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_chain(self) -> "TurnRunApprovalChainReadModel":
        validate_execution_ref(self.contract_ref, "contract_ref")
        validate_execution_ref(self.chain_ref, "chain_ref")
        validate_execution_ref(self.cli_ref, "cli_ref")
        validate_execution_ref(self.api_read_model_ref, "api_read_model_ref")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        if self.canonical_states != list(TURN_RUN_APPROVAL_CANONICAL_STATES):
            raise ValueError("turn/run approval chain canonical states drifted")
        if self.transitions:
            if self.current_state != self.transitions[-1].to_state:
                raise ValueError("turn/run approval current state must match the latest transition")
            previous = self.transitions[0].from_state
            for transition in self.transitions:
                if transition.from_state != previous:
                    raise ValueError("turn/run approval transitions must be sequential")
                if transition.to_state not in TURN_RUN_APPROVAL_ALLOWED_TRANSITIONS[TurnRunApprovalState(transition.from_state)]:
                    raise ValueError("turn/run approval transition sequence is not allowed")
                previous = transition.to_state
        elif self.current_state != TurnRunApprovalState.created.value:
            raise ValueError("turn/run approval chain without transitions must be created")
        if not self.safe_refs_only:
            raise ValueError("turn/run approval chain must be safe-ref only")
        if (
            self.raw_payloads_persisted
            or self.approval_ref_grants_authority
            or self.execution_enabled
            or self.execution_performed
            or self.background_autonomy_enabled
        ):
            raise ValueError("turn/run approval chain cannot grant authority, execute, or persist raw payloads")
        return self


def build_empty_turn_run_approval_chain(
    *,
    chain_ref: str,
    durable_run_ref: str,
    turn_ref: str | None = None,
    operator_task_ref: str | None = None,
    approval_ref: str | None = None,
    route_decision_binding_ref: str | None = None,
) -> TurnRunApprovalChainReadModel:
    linkage = TurnRunApprovalLinkage(
        turn_ref=TurnRef(ref=turn_ref) if turn_ref else None,
        durable_run_ref=DurableRunRef(ref=durable_run_ref),
        operator_task_ref=operator_task_ref,
        approval_ref=ApprovalRef(ref=approval_ref) if approval_ref else None,
        route_decision_binding_ref=(
            RouteDecisionBindingRef(ref=route_decision_binding_ref) if route_decision_binding_ref else None
        ),
        evidence_refs=["evidence-ref:turn-run-approval-chain:created"],
    )
    return TurnRunApprovalChainReadModel(
        chain_ref=chain_ref,
        current_state=TurnRunApprovalState.created,
        linkage=linkage,
    )


def apply_turn_run_approval_transition(
    chain: TurnRunApprovalChainReadModel,
    request: TurnRunApprovalTransitionRequest,
) -> tuple[TurnRunApprovalChainReadModel, TurnRunApprovalTransitionDecision]:
    fingerprint_ref = _request_fingerprint_ref(request)
    existing = _find_idempotency_record(chain, request.idempotency_key)
    if existing is not None:
        if existing.request_fingerprint_ref == fingerprint_ref:
            return chain, _decision(
                request,
                TurnRunApprovalTransitionStatus.idempotent_replay,
                chain.current_state,
                chain.current_state,
                ["reason-ref:turn-run-chain:idempotent-replay"],
                "Turn/run approval transition was already applied; chain truth is unchanged.",
                fingerprint_ref,
            )
        return chain, _decision(
            request,
            TurnRunApprovalTransitionStatus.denied,
            chain.current_state,
            chain.current_state,
            ["reason-ref:turn-run-chain:idempotency-conflict"],
            "Turn/run approval transition was denied by idempotency conflict.",
            fingerprint_ref,
        )
    reasons = _transition_denial_reasons(chain, request)
    if reasons:
        return chain, _decision(
            request,
            TurnRunApprovalTransitionStatus.denied,
            chain.current_state,
            chain.current_state,
            reasons,
            "Turn/run approval transition was denied by chain policy.",
            fingerprint_ref,
        )
    transition = TurnRunApprovalTransition(
        transition_ref=request.transition_ref,
        from_state=request.from_state,
        to_state=request.to_state,
        actor_ref=request.actor_ref,
        idempotency_key=request.idempotency_key,
        checkpoint_ref=CheckpointRef(ref=request.checkpoint_ref) if request.checkpoint_ref else None,
        receipt_ref=ReceiptRef(ref=request.receipt_ref),
        replay_ref=request.replay_ref,
        approval_ref=ApprovalRef(ref=request.approval_ref) if request.approval_ref else None,
        route_decision_binding_ref=(
            RouteDecisionBindingRef(ref=request.route_decision_binding_ref) if request.route_decision_binding_ref else None
        ),
        evidence_refs=request.evidence_refs,
        reason_refs=request.reason_refs,
        safe_summary=request.safe_summary,
    )
    idempotency_record = TurnRunApprovalIdempotencyRecord(
        idempotency_key=request.idempotency_key,
        request_fingerprint_ref=fingerprint_ref,
        transition_ref=request.transition_ref,
        accepted_state_before=chain.current_state,
        accepted_state_after=request.to_state,
        receipt_ref=request.receipt_ref,
        replay_ref=request.replay_ref,
    )
    payload = chain.model_dump(mode="python")
    payload["current_state"] = request.to_state
    payload["transitions"] = [*chain.transitions, transition]
    payload["idempotency_records"] = [*chain.idempotency_records, idempotency_record]
    updated = TurnRunApprovalChainReadModel(**payload)
    return updated, _decision(
        request,
        TurnRunApprovalTransitionStatus.accepted,
        chain.current_state,
        request.to_state,
        ["reason-ref:turn-run-chain:accepted"],
        "Turn/run approval transition was accepted as state-only chain truth.",
        fingerprint_ref,
    )


def build_sample_turn_run_approval_chain() -> TurnRunApprovalChainReadModel:
    chain = build_empty_turn_run_approval_chain(
        chain_ref="turn-run-chain:sample-runtime-parity",
        turn_ref="turn-ref:sample-runtime-parity",
        durable_run_ref="durable-run-ref:sample-runtime-parity",
        approval_ref="approval-ref:sample-runtime-parity",
        route_decision_binding_ref="route-decision-binding-ref:sample-runtime-parity",
    )
    for to_state in (
        TurnRunApprovalState.routed,
        TurnRunApprovalState.planning,
        TurnRunApprovalState.waiting_for_approval,
    ):
        chain, decision = apply_turn_run_approval_transition(
            chain,
            TurnRunApprovalTransitionRequest(
                transition_ref=f"turn-run-transition:sample-{to_state.value}",
                from_state=chain.current_state,
                to_state=to_state,
                actor_ref="actor-ref:sample-runtime-parity",
                idempotency_key=f"idempotency-ref:sample-{to_state.value}",
                checkpoint_ref=f"checkpoint-ref:sample-{to_state.value}",
                receipt_ref=f"receipt-ref:sample-{to_state.value}",
                replay_ref=f"replay-ref:sample-{to_state.value}",
                approval_ref="approval-ref:sample-runtime-parity"
                if to_state == TurnRunApprovalState.waiting_for_approval
                else None,
                approval_scope_run_ref="durable-run-ref:sample-runtime-parity"
                if to_state == TurnRunApprovalState.waiting_for_approval
                else None,
                approval_scope_turn_ref="turn-ref:sample-runtime-parity"
                if to_state == TurnRunApprovalState.waiting_for_approval
                else None,
                route_decision_binding_ref="route-decision-binding-ref:sample-runtime-parity",
                evidence_refs=[f"evidence-ref:sample-{to_state.value}"],
                reason_refs=[f"reason-ref:sample-{to_state.value}"],
                safe_summary="Sample chain recorded state-only runtime parity posture.",
            ),
        )
        if decision.status != TurnRunApprovalTransitionStatus.accepted.value:
            raise ValueError("sample turn/run approval chain transition failed")
    return chain


def _transition_denial_reasons(
    chain: TurnRunApprovalChainReadModel,
    request: TurnRunApprovalTransitionRequest,
) -> list[str]:
    reasons: list[str] = []
    if request.execution_requested:
        reasons.append("reason-ref:turn-run-chain:execution-requested-denied")
    if request.background_autonomy_requested:
        reasons.append("reason-ref:turn-run-chain:background-autonomy-denied")
    if request.raw_payloads_included:
        reasons.append("reason-ref:turn-run-chain:raw-payload-denied")
    if request.from_state != chain.current_state:
        reasons.append("reason-ref:turn-run-chain:stale-state")
    if chain.current_state in TURN_RUN_APPROVAL_TERMINAL_STATES:
        reasons.append("reason-ref:turn-run-chain:terminal-state")
    if request.to_state not in TURN_RUN_APPROVAL_ALLOWED_TRANSITIONS[TurnRunApprovalState(chain.current_state)]:
        reasons.append("reason-ref:turn-run-chain:invalid-transition")
    if request.to_state in {
        TurnRunApprovalState.approved.value,
        TurnRunApprovalState.running.value,
        TurnRunApprovalState.resumed.value,
    }:
        reasons.extend(_approval_scope_reasons(chain, request))
    if request.to_state == TurnRunApprovalState.blocked.value and not request.reason_refs:
        reasons.append("reason-ref:turn-run-chain:blocked-reason-required")
    return dedupe_reasons(reasons)


def _approval_scope_reasons(
    chain: TurnRunApprovalChainReadModel,
    request: TurnRunApprovalTransitionRequest,
) -> list[str]:
    reasons: list[str] = []
    linkage = chain.linkage
    if request.approval_ref is None:
        reasons.append("reason-ref:turn-run-chain:approval-ref-required")
    elif linkage.approval_ref is not None and request.approval_ref != linkage.approval_ref.ref:
        reasons.append("reason-ref:turn-run-chain:approval-ref-mismatch")
    if request.approval_scope_run_ref != linkage.durable_run_ref.ref:
        reasons.append("reason-ref:turn-run-chain:approval-run-scope-mismatch")
    if linkage.turn_ref is not None and request.approval_scope_turn_ref != linkage.turn_ref.ref:
        reasons.append("reason-ref:turn-run-chain:approval-turn-scope-mismatch")
    if (
        linkage.route_decision_binding_ref is not None
        and request.route_decision_binding_ref != linkage.route_decision_binding_ref.ref
    ):
        reasons.append("reason-ref:turn-run-chain:route-binding-scope-mismatch")
    return reasons


def _decision(
    request: TurnRunApprovalTransitionRequest,
    status: TurnRunApprovalTransitionStatus,
    previous_state: TurnRunApprovalState,
    next_state: TurnRunApprovalState,
    reason_refs: list[str],
    safe_summary: str,
    fingerprint_ref: str,
) -> TurnRunApprovalTransitionDecision:
    return TurnRunApprovalTransitionDecision(
        decision_ref=_stable_ref("turn-run-chain-decision", request.transition_ref, status.value),
        status=status,
        previous_state=previous_state,
        next_state=next_state,
        reason_refs=reason_refs,
        safe_summary=safe_summary,
        request_fingerprint_ref=fingerprint_ref,
        receipt_ref=request.receipt_ref,
        replay_ref=request.replay_ref,
    )


def _find_idempotency_record(
    chain: TurnRunApprovalChainReadModel,
    idempotency_key: str,
) -> TurnRunApprovalIdempotencyRecord | None:
    for record in chain.idempotency_records:
        if record.idempotency_key == idempotency_key:
            return record
    return None


def _request_fingerprint_ref(request: TurnRunApprovalTransitionRequest) -> str:
    return _stable_ref("turn-run-chain-request-fingerprint", json.dumps(request.model_dump(mode="json"), sort_keys=True))


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value is not None:
        validate_execution_ref(value, field_name)
