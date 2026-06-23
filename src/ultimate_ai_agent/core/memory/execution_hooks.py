from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.time import utc_now


MEMORY_EXECUTION_HOOK_CONTRACT_REF = (
    "contract-ref:governed-cognitive-memory-spine:phase6-execution-hooks:v1"
)
MEMORY_EXECUTION_HOOK_STATUS = "future_blocked_contract_only"
MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS = (
    "blocked-state:memory-execution-no-automatic-execution",
    "blocked-state:memory-execution-no-action-execution",
    "blocked-state:memory-execution-no-connector-writes",
    "blocked-state:memory-execution-no-crm-sync",
    "blocked-state:memory-execution-no-account-sync",
    "blocked-state:memory-execution-no-shell-subprocess",
    "blocked-state:memory-execution-no-browser-automation",
    "blocked-state:memory-execution-no-provider-or-model-calls",
    "blocked-state:memory-execution-no-hidden-context-injection",
    "blocked-state:memory-execution-no-memory-truth-authority",
    "blocked-state:memory-execution-no-unreviewed-recall",
    "blocked-state:memory-execution-no-broad-autonomy",
    "blocked-state:memory-execution-no-public-beta",
    "blocked-state:memory-execution-no-production-authority",
)
MEMORY_EXECUTION_HOOK_REQUIRED_FLOW_REFS = (
    "required-flow-ref:context-pack-proposal",
    "required-flow-ref:action-envelope",
    "required-flow-ref:exact-local-approval-authority-scope",
    "required-flow-ref:idempotency",
    "required-flow-ref:durable-receipt",
    "required-flow-ref:rollback-or-safe-disable",
    "required-flow-ref:evidence-timeline-event",
)

MemoryExecutionHookStatus = Literal[
    "blocked",
    "future_blocked_contract_only",
    "proposal_only_blocked",
]
MemoryExecutionHookRiskClass = Literal["low", "medium", "high"]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw-prompt",
    "raw response",
    "raw_response",
    "raw-response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw transcript",
    "raw_transcript",
    "raw-transcript",
    "raw source",
    "raw_source",
    "raw-source",
    "raw file",
    "raw_file",
    "raw-file",
    "raw path",
    "raw_path",
    "raw-path",
    "raw log",
    "raw_log",
    "raw-log",
    "private ui content",
    "private_ui_content",
    "private-ui-content",
    "username",
    "hostname",
    "credential",
    "password",
    "secret",
    "api key",
    "api_key",
    "token",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)
_DENIED_AUTHORITY_FLAGS = (
    "runtime_execution_authorized",
    "automatic_execution_authorized",
    "action_execution_authorized",
    "automatic_action_execution_authorized",
    "automatic_memory_write_authorized",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "shell_subprocess_authorized",
    "browser_automation_authorized",
    "provider_model_call_authorized",
    "hidden_context_injection_authorized",
    "automatic_context_injection_authorized",
    "context_pack_injection_authorized",
    "memory_truth_authority_enabled",
    "unreviewed_recall_allowed",
    "broad_autonomy_enabled",
    "public_beta_enabled",
    "production_authority_enabled",
    "runtime_route_registered",
    "background_agent_enabled",
    "automatic_scheduling_enabled",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe memory execution content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)
    _validate_safe_text(value, field_name)


class _MemoryExecutionHookAuthorityPosture(BaseModel):
    runtime_execution_authorized: bool = False
    automatic_execution_authorized: bool = False
    action_execution_authorized: bool = False
    automatic_action_execution_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    connector_write_authorized: bool = False
    external_crm_sync_authorized: bool = False
    account_sync_authorized: bool = False
    shell_subprocess_authorized: bool = False
    browser_automation_authorized: bool = False
    provider_model_call_authorized: bool = False
    hidden_context_injection_authorized: bool = False
    automatic_context_injection_authorized: bool = False
    context_pack_injection_authorized: bool = False
    memory_truth_authority_enabled: bool = False
    unreviewed_recall_allowed: bool = False
    broad_autonomy_enabled: bool = False
    public_beta_enabled: bool = False
    production_authority_enabled: bool = False
    runtime_route_registered: bool = False
    background_agent_enabled: bool = False
    automatic_scheduling_enabled: bool = False


class MemoryExecutionHookBlockedState(BaseModel):
    blocked_state_ref: str = Field(..., min_length=1)
    reason_ref: str = Field(..., min_length=1)
    evidence_requirement_refs: list[str] = Field(default_factory=list)
    current_status: MemoryExecutionHookStatus = "blocked"

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_blocked_state(self) -> "MemoryExecutionHookBlockedState":
        _validate_safe_ref(self.blocked_state_ref, "blocked_state_ref")
        _validate_safe_ref(self.reason_ref, "reason_ref")
        for ref in self.evidence_requirement_refs:
            _validate_safe_ref(ref, "evidence_requirement_refs")
        return self


def _default_blocked_states() -> list[MemoryExecutionHookBlockedState]:
    return [
        MemoryExecutionHookBlockedState(
            blocked_state_ref=ref,
            reason_ref=f"reason-ref:{ref.split(':', 1)[1]}",
            evidence_requirement_refs=[
                "evidence-requirement-ref:future-accepted-exact-scope",
                "evidence-requirement-ref:future-receipt-rollback-proof",
            ],
        )
        for ref in MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS
    ]


class MemoryExecutionHookContract(_MemoryExecutionHookAuthorityPosture):
    contract_ref: str = MEMORY_EXECUTION_HOOK_CONTRACT_REF
    status: MemoryExecutionHookStatus = MEMORY_EXECUTION_HOOK_STATUS
    source_context_pack_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    exact_approval_scope_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    durable_receipt_ref: str = Field(..., min_length=1)
    evidence_timeline_event_ref: str = Field(..., min_length=1)
    required_flow_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_EXECUTION_HOOK_REQUIRED_FLOW_REFS)
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS)
    )
    blocked_states: list[MemoryExecutionHookBlockedState] = Field(
        default_factory=_default_blocked_states
    )
    contract_only: bool = True
    safe_refs_only: bool = True
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_contract(self) -> "MemoryExecutionHookContract":
        for field_name in [
            "contract_ref",
            "source_context_pack_ref",
            "action_envelope_ref",
            "exact_approval_scope_ref",
            "idempotency_ref",
            "rollback_ref",
            "safe_disable_ref",
            "durable_receipt_ref",
            "evidence_timeline_event_ref",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.status, "status")
        for field_name in ["required_flow_refs", "blocked_authority_refs"]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if self.status == "blocked":
            raise ValueError("Phase 6 contract must stay future-blocked, not active")
        if not self.contract_only:
            raise ValueError("Phase 6 must remain contract-only")
        if not self.safe_refs_only:
            raise ValueError("Phase 6 contract must use safe refs only")
        _raise_for_authority_flags(self, "Phase 6 memory execution contract")
        return self


class MemoryExecutionHookProposal(_MemoryExecutionHookAuthorityPosture):
    proposal_ref: str = Field(..., min_length=1)
    contract_ref: str = MEMORY_EXECUTION_HOOK_CONTRACT_REF
    context_pack_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    exact_approval_scope_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    durable_receipt_ref: str = Field(..., min_length=1)
    evidence_timeline_event_ref: str = Field(..., min_length=1)
    source_memory_record_refs: list[str] = Field(default_factory=list)
    context_pack_proposal_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(MEMORY_EXECUTION_HOOK_BLOCKED_STATE_REFS)
    )
    risk_class: MemoryExecutionHookRiskClass = "low"
    proposal_only: bool = True
    execution_blocked: bool = True
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "MemoryExecutionHookProposal":
        for field_name in [
            "proposal_ref",
            "contract_ref",
            "context_pack_ref",
            "action_envelope_ref",
            "exact_approval_scope_ref",
            "idempotency_ref",
            "rollback_ref",
            "safe_disable_ref",
            "durable_receipt_ref",
            "evidence_timeline_event_ref",
        ]:
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        _validate_safe_text(self.risk_class, "risk_class")
        for field_name in [
            "source_memory_record_refs",
            "context_pack_proposal_refs",
            "blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if not self.context_pack_proposal_refs:
            raise ValueError("memory execution proposals require context-pack refs")
        if not self.proposal_only:
            raise ValueError("memory execution hooks must remain proposal-only")
        if not self.execution_blocked:
            raise ValueError("memory execution hooks must remain blocked")
        _raise_for_authority_flags(self, "Phase 6 memory execution proposal")
        return self


def _raise_for_authority_flags(
    model: _MemoryExecutionHookAuthorityPosture,
    label: str,
) -> None:
    for flag in _DENIED_AUTHORITY_FLAGS:
        if bool(getattr(model, flag)):
            raise ValueError(f"{flag} must remain false for {label}")
