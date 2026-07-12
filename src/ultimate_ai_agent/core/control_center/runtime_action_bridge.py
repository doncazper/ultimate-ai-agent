from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway import RuntimeInvocationRecord
from ultimate_ai_agent.core.runtime_gateway.action_evidence import (
    build_runtime_action_signed_evidence,
    verify_runtime_action_signed_evidence,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF,
    GOVERNED_RUNTIME_SAFE_DISABLE_REF,
    RuntimeSafeDisableState,
)


RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF = (
    "contract-ref:governed-runtime-action-inbox-execution-bridge:v1"
)
RUNTIME_ACTION_INBOX_BRIDGE_SOURCE = (
    "python_core_runtime_gateway_action_inbox_bridge_read_model"
)
RUNTIME_ACTION_INBOX_BRIDGE_CLI_REF = (
    "uaa runtime inspect-action-inbox-bridge"
)
RUNTIME_ACTION_INBOX_BRIDGE_ROUTE_REF = "GET /control-center/actions/inbox"
RUNTIME_PARITY_LOOP_API_ROUTE_REF = "GET /api/runtime/parity-loop"
RUNTIME_PARITY_LOOP_CLI_REF = "uaa runtime inspect-parity-loop"
RUNTIME_PARITY_LOOP_STAGE_REFS = (
    "runtime-loop-stage-ref:prepared-turn",
    "runtime-loop-stage-ref:route-decision-binding",
    "runtime-loop-stage-ref:durable-run-approval",
    "runtime-loop-stage-ref:staged-orchestration",
    "runtime-loop-stage-ref:role-provider-evidence",
    "runtime-loop-stage-ref:action-inbox-approval",
    "runtime-loop-stage-ref:exact-action-receipt",
    "runtime-loop-stage-ref:signed-evidence",
    "runtime-loop-stage-ref:blocked-retry-state",
)
RUNTIME_ACTION_INBOX_BRIDGE_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:runtime-unrestricted-command-execution",
    "blocked-authority:runtime-command-execution-without-gateway-allowlist",
    "blocked-authority:runtime-command-network-access",
    "blocked-authority:runtime-browser-automation",
    "blocked-authority:runtime-connector-write",
    "blocked-authority:runtime-plugin-import",
    "blocked-authority:runtime-remote-execution",
    "blocked-authority:runtime-remote-provider-model-call",
    "blocked-authority:runtime-production-authority",
)
RUNTIME_ACTION_INBOX_BRIDGE_EVENT_KINDS = {
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
}
DEFAULT_SAFE_DISABLE_REASON_REF = "reason-ref:governed-runtime-phase-02-disabled"


def _runtime_value(value: Any) -> Any:
    return getattr(value, "value", value)


class RuntimeActionInboxBridgeItem(BaseModel):
    invocation_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    adapter_id: str = Field(..., min_length=1, max_length=120)
    requested_authority: str = Field(..., min_length=1, max_length=120)
    command_intent: str | None = None
    status: str = Field(..., min_length=1, max_length=120)
    approval_validated: bool = False
    authority_scope_required: bool = True
    authority_scope_allowed: bool = False
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain_ref: str | None = None
    authority_capability_ref: str | None = None
    authority_required_mode_ref: str | None = None
    authority_reason_refs: list[str] = Field(default_factory=list)
    authority_audit_ref: str | None = None
    authority_policy_receipt_ref: str | None = None
    authority_operator_message: str | None = None
    execution_performed: bool = False
    exact_scope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_decision_ref: str | None = None
    approval_validation_ref: str | None = None
    idempotency_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    safe_disable_posture_ref: str = Field(..., min_length=1)
    receipt_ref: str | None = None
    execution_result_ref: str | None = None
    signed_evidence_ref: str | None = None
    signed_evidence_verifier_ref: str | None = None
    signed_evidence_verification_status: str = "not_available"
    receipt_status: str = "receipt_not_recorded"
    exit_code: int | None = None
    timed_out: bool = False
    command_output_persisted: bool = False
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_reason_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "RuntimeActionInboxBridgeItem":
        for value, field_name in [
            (self.invocation_ref, "invocation_ref"),
            (self.action_envelope_ref, "action_envelope_ref"),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.approval_ref, "approval_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.execution_result_ref, "execution_result_ref"),
            (self.signed_evidence_ref, "signed_evidence_ref"),
            (self.signed_evidence_verifier_ref, "signed_evidence_verifier_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.authority_lease_ref, "authority_lease_ref"),
            (self.authority_domain_ref, "authority_domain_ref"),
            (self.authority_capability_ref, "authority_capability_ref"),
            (self.authority_required_mode_ref, "authority_required_mode_ref"),
            (self.authority_audit_ref, "authority_audit_ref"),
            (self.authority_policy_receipt_ref, "authority_policy_receipt_ref"),
        ]:
            if value is not None:
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.adapter_id, "adapter_id"),
            (self.requested_authority, "requested_authority"),
            (self.command_intent or "not_applicable", "command_intent"),
            (self.status, "status"),
            (
                self.authority_decision_outcome or "authority-decision-outcome:none",
                "authority_decision_outcome",
            ),
            (
                self.authority_operator_message or "authority-message:none",
                "authority_operator_message",
            ),
            (self.signed_evidence_verification_status, "signed_evidence_verification_status"),
            (self.receipt_status, "receipt_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        if self.command_output_persisted:
            raise ValueError("Runtime bridge item must not persist command output")
        for field_name in (
            "receipt_refs",
            "evidence_refs",
            "authority_reason_refs",
            "blocked_reason_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        return self


class RuntimeActionInboxBridgeEvidenceItem(BaseModel):
    event_ref: str = Field(..., min_length=1)
    event_kind: str = Field(..., min_length=1, max_length=120)
    invocation_ref: str = Field(..., min_length=1)
    receipt_ref: str | None = None
    policy_decision_ref: str | None = None
    action_envelope_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=420)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_evidence_item(self) -> "RuntimeActionInboxBridgeEvidenceItem":
        for value, field_name in [
            (self.event_ref, "event_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.action_envelope_ref, "action_envelope_ref"),
        ]:
            if value is not None:
                validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.event_kind, "event_kind")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.event_kind not in RUNTIME_ACTION_INBOX_BRIDGE_EVENT_KINDS:
            raise ValueError("Runtime bridge event kind is not recognized")
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        return self


class RuntimeActionInboxBridgeReadModel(BaseModel):
    schema_version: str = "governed-runtime-action-inbox-bridge.v1"
    contract_ref: str = RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF
    source: str = RUNTIME_ACTION_INBOX_BRIDGE_SOURCE
    backend_owned: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    route_ref: str = RUNTIME_ACTION_INBOX_BRIDGE_ROUTE_REF
    cli_ref: str = RUNTIME_ACTION_INBOX_BRIDGE_CLI_REF
    runtime_parity_loop_api_ref: str = RUNTIME_PARITY_LOOP_API_ROUTE_REF
    runtime_parity_loop_cli_ref: str = RUNTIME_PARITY_LOOP_CLI_REF
    runtime_parity_loop_status: str = (
        "backend_owned_runtime_parity_loop_available"
    )
    runtime_parity_loop_stage_refs: list[str] = Field(
        default_factory=lambda: list(RUNTIME_PARITY_LOOP_STAGE_REFS)
    )
    status_cli_ref: str = "uaa runtime status"
    capabilities_cli_ref: str = "uaa runtime capabilities"
    invocations_cli_ref: str = "uaa runtime invocations list"
    receipts_cli_ref: str = "uaa runtime receipts show"
    signed_evidence_cli_ref: str = "uaa runtime receipts evidence"
    signed_evidence_verifier_cli_ref: str = "uaa runtime receipts verify-evidence"
    safe_disable_cli_ref: str = "uaa runtime safe-disable"
    status: str = "backend_owned_runtime_action_inbox_bridge"
    runtime_status_ref: str = "runtime-status-ref:governed-runtime-pilot"
    default_profile: str = "sealed"
    runtime_profile_status: str = "sealed_default"
    local_model_readiness: str = "configured_loopback_available_when_enabled"
    command_runtime_readiness: str = "utility_command_requires_action_inbox_approval"
    safe_disable_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_REF
    safe_disable_posture_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF
    safe_disable_active: bool = True
    safe_disable_summary: str = "Governed runtime is sealed by default."
    item_count: int = Field(ge=0)
    pending_approval_count: int = Field(ge=0)
    approved_pending_execution_count: int = Field(ge=0)
    receipt_recorded_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    item_refs: list[str] = Field(default_factory=list)
    approval_envelope_refs: list[str] = Field(default_factory=list)
    pending_runtime_approval_refs: list[str] = Field(default_factory=list)
    execution_result_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    signed_evidence_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    items: list[RuntimeActionInboxBridgeItem] = Field(default_factory=list)
    evidence_timeline: list[RuntimeActionInboxBridgeEvidenceItem] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Inspect exact runtime approval envelopes and receipts; broad runtime authority remains blocked."
    )
    operator_summary: str = Field(..., min_length=1, max_length=700)
    action_execution_enabled: bool = False
    arbitrary_command_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    browser_execution_enabled: bool = False
    connector_write_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_model(self) -> "RuntimeActionInboxBridgeReadModel":
        if self.schema_version != "governed-runtime-action-inbox-bridge.v1":
            raise ValueError("Runtime Action Inbox bridge schema drift")
        if self.contract_ref != RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF:
            raise ValueError("Runtime Action Inbox bridge contract drift")
        if self.source != RUNTIME_ACTION_INBOX_BRIDGE_SOURCE:
            raise ValueError("Runtime Action Inbox bridge source drift")
        if not self.backend_owned or not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Runtime Action Inbox bridge must stay safe-ref only")
        if self.item_count != len(self.items):
            raise ValueError("Runtime Action Inbox bridge item count drift")
        if self.item_refs != [item.invocation_ref for item in self.items]:
            raise ValueError("Runtime Action Inbox bridge item ref drift")
        for field_name in (
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
            "default_profile",
            "runtime_profile_status",
            "local_model_readiness",
            "command_runtime_readiness",
            "safe_disable_summary",
            "next_safe_action",
            "operator_summary",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "runtime_status_ref",
            "safe_disable_ref",
            "safe_disable_posture_ref",
        ):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "item_refs",
            "approval_envelope_refs",
            "pending_runtime_approval_refs",
            "execution_result_refs",
            "receipt_refs",
            "signed_evidence_refs",
            "evidence_refs",
            "runtime_parity_loop_stage_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for flag in (
            "action_execution_enabled",
            "arbitrary_command_execution_enabled",
            "provider_model_call_enabled",
            "browser_execution_enabled",
            "connector_write_enabled",
            "production_authority_enabled",
        ):
            if getattr(self, flag):
                raise ValueError(f"Runtime Action Inbox bridge must not enable {flag}")
        return self


def build_runtime_action_inbox_bridge_read_model(
    records: list[RuntimeInvocationRecord],
    *,
    entries: list[Any] | None = None,
) -> dict[str, Any]:
    items = [_item_for_record(record) for record in records if record.action_inbox_envelope]
    receipt_refs = list(dict.fromkeys(ref for item in items for ref in item.receipt_refs))
    signed_evidence_refs = list(
        dict.fromkeys(
            ref for item in items for ref in [item.signed_evidence_ref] if ref is not None
        )
    )
    evidence_refs = list(dict.fromkeys(ref for item in items for ref in item.evidence_refs))
    execution_result_refs = list(
        dict.fromkeys(
            ref
            for item in items
            for ref in [item.execution_result_ref]
            if ref is not None
        )
    )
    evidence_timeline = (
        _evidence_timeline_for_entries(entries)
        if entries is not None
        else _evidence_timeline_for_records(records)
    )
    safe_disable = _safe_disable_state(records)
    blocked_count = sum(
        1
        for item in items
        if item.status
        in {
            "execution_blocked",
            "approval_denied",
            "approval_expired",
            "safe_disabled",
        }
    )
    model = RuntimeActionInboxBridgeReadModel(
        runtime_profile_status=_runtime_profile_status(records),
        local_model_readiness=_local_model_readiness(records),
        command_runtime_readiness=_command_runtime_readiness(items),
        safe_disable_ref=safe_disable.safe_disable_ref,
        safe_disable_posture_ref=safe_disable.safe_disable_posture_ref,
        safe_disable_active=bool(safe_disable.active),
        safe_disable_summary=safe_disable.safe_summary,
        item_count=len(items),
        pending_approval_count=sum(1 for item in items if item.status == "pending_approval"),
        approved_pending_execution_count=sum(
            1 for item in items if item.status == "approved_pending_execution"
        ),
        receipt_recorded_count=sum(1 for item in items if item.status == "receipt_recorded"),
        blocked_count=blocked_count,
        item_refs=[item.invocation_ref for item in items],
        approval_envelope_refs=[item.action_envelope_ref for item in items],
        pending_runtime_approval_refs=[
            item.approval_ref
            for item in items
            if item.status in {"pending_approval", "approved_pending_execution"}
        ],
        execution_result_refs=execution_result_refs,
        receipt_refs=receipt_refs,
        signed_evidence_refs=signed_evidence_refs,
        evidence_refs=evidence_refs,
        runtime_parity_loop_stage_refs=list(RUNTIME_PARITY_LOOP_STAGE_REFS),
        items=items,
        evidence_timeline=evidence_timeline,
        blocked_authority_refs=list(RUNTIME_ACTION_INBOX_BRIDGE_BLOCKED_AUTHORITY_REFS),
        operator_summary=(
            f"{len(items)} governed runtime approval envelopes are visible with "
            f"{len(receipt_refs)} receipt refs, {len(signed_evidence_refs)} local "
            "hash-integrity evidence refs (legacy signed identifiers), "
            f"{len(evidence_refs)} evidence refs, "
            f"and {len(evidence_timeline)} timeline events."
        ),
    )
    return model.model_dump(mode="json")


def _item_for_record(record: RuntimeInvocationRecord) -> RuntimeActionInboxBridgeItem:
    envelope = record.action_inbox_envelope
    if envelope is None:  # pragma: no cover - filtered by caller
        raise ValueError("Runtime Action Inbox envelope missing")
    receipt_refs = list(envelope.receipt_refs)
    evidence_refs = list(envelope.evidence_refs)
    receipt_ref = None
    execution_result_ref = None
    receipt_status = "receipt_not_recorded"
    signed_evidence_ref = None
    signed_evidence_verifier_ref = None
    signed_evidence_verification_status = "not_available"
    exit_code = None
    timed_out = False
    if record.receipt is not None:
        receipt_ref = record.receipt.receipt_ref
        receipt_status = str(_runtime_value(record.receipt.invocation_status))
        receipt_refs = list(dict.fromkeys([*receipt_refs, record.receipt.receipt_ref]))
        evidence_refs = list(dict.fromkeys([*evidence_refs, *record.receipt.evidence_refs]))
        if record.receipt.command_receipt_metadata is not None:
            metadata = record.receipt.command_receipt_metadata
            execution_result_ref = metadata.redacted_output_ref
            exit_code = metadata.exit_code
            timed_out = metadata.timed_out
        signed_evidence = _signed_evidence_for_record(record)
        if signed_evidence is not None:
            signed_evidence_ref = signed_evidence["signed_evidence_ref"]
            signed_evidence_verifier_ref = signed_evidence["verifier_ref"]
            signed_evidence_verification_status = signed_evidence["verification_status"]
    return RuntimeActionInboxBridgeItem(
        invocation_ref=record.invocation_ref,
        action_envelope_ref=envelope.action_envelope_ref,
        adapter_id=envelope.adapter_id,
        requested_authority=str(_runtime_value(envelope.requested_authority)),
        command_intent=(
            str(_runtime_value(envelope.command_intent))
            if envelope.command_intent
            else None
        ),
        status=str(_runtime_value(record.status)),
        approval_validated=bool(envelope.approval_validated),
        authority_scope_required=bool(envelope.authority_scope_required),
        authority_scope_allowed=bool(envelope.authority_scope_allowed),
        authority_decision_ref=envelope.authority_decision_ref,
        authority_decision_outcome=envelope.authority_decision_outcome,
        authority_lease_ref=envelope.authority_lease_ref,
        authority_domain_ref=envelope.authority_domain_ref,
        authority_capability_ref=envelope.authority_capability_ref,
        authority_required_mode_ref=envelope.authority_required_mode_ref,
        authority_reason_refs=list(envelope.authority_reason_refs),
        authority_audit_ref=envelope.authority_audit_ref,
        authority_policy_receipt_ref=envelope.authority_policy_receipt_ref,
        authority_operator_message=envelope.authority_operator_message,
        execution_performed=bool(record.receipt and record.receipt.execution_performed),
        exact_scope_ref=envelope.exact_scope_ref,
        approval_ref=envelope.approval_ref,
        approval_decision_ref=envelope.approval_decision_ref,
        approval_validation_ref=envelope.approval_validation_ref,
        idempotency_ref=envelope.idempotency_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        payload_fingerprint_ref=record.payload_fingerprint_ref,
        rollback_ref=envelope.rollback_ref,
        safe_disable_ref=envelope.safe_disable_ref,
        safe_disable_posture_ref=envelope.safe_disable_posture_ref,
        receipt_ref=receipt_ref,
        execution_result_ref=execution_result_ref,
        signed_evidence_ref=signed_evidence_ref,
        signed_evidence_verifier_ref=signed_evidence_verifier_ref,
        signed_evidence_verification_status=signed_evidence_verification_status,
        receipt_status=receipt_status,
        exit_code=exit_code,
        timed_out=timed_out,
        command_output_persisted=False,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        blocked_reason_refs=list(envelope.blocked_reason_refs),
        blocked_authority_refs=list(RUNTIME_ACTION_INBOX_BRIDGE_BLOCKED_AUTHORITY_REFS),
        safe_summary=(
            "Exact governed runtime envelope is inspectable through Action Inbox; "
            "broad runtime authority remains blocked."
        ),
    )


def _signed_evidence_for_record(record: RuntimeInvocationRecord) -> dict[str, str] | None:
    if record.receipt is None:
        return None
    try:
        envelope = build_runtime_action_signed_evidence(record)
        verification = verify_runtime_action_signed_evidence(envelope)
    except ValueError:
        return None
    return {
        "signed_evidence_ref": envelope.signed_envelope_ref,
        "verifier_ref": envelope.verifier_ref,
        "verification_status": verification.verification_status,
    }


def _safe_disable_state(records: list[RuntimeInvocationRecord]) -> RuntimeSafeDisableState:
    for record in reversed(records):
        if record.safe_disable.active:
            return record.safe_disable
    if records:
        return records[-1].safe_disable
    return RuntimeSafeDisableState()


def _runtime_profile_status(records: list[RuntimeInvocationRecord]) -> str:
    statuses = {str(_runtime_value(record.status)) for record in records}
    if "receipt_recorded" in statuses:
        return "receipt_recorded_runtime_activity"
    if "approved_pending_execution" in statuses:
        return "operator_approved_pending_execution"
    if records:
        return "runtime_invocations_recorded"
    return "sealed_default"


def _local_model_readiness(records: list[RuntimeInvocationRecord]) -> str:
    if any(
        record.receipt is not None and record.receipt.model_call_performed
        for record in records
    ):
        return "local_model_runtime_receipt_recorded"
    return "configured_loopback_available_when_enabled"


def _command_runtime_readiness(items: list[RuntimeActionInboxBridgeItem]) -> str:
    if any(item.execution_performed for item in items):
        return "utility_command_receipt_recorded"
    if any(item.approval_validated for item in items):
        return "utility_command_approved_pending_execution"
    if items:
        return "utility_command_approval_envelopes_visible"
    return "utility_command_requires_action_inbox_approval"


def _evidence_timeline_for_entries(
    entries: list[Any],
) -> list[RuntimeActionInboxBridgeEvidenceItem]:
    timeline: list[RuntimeActionInboxBridgeEvidenceItem] = []
    seen: set[tuple[str, str]] = set()
    for entry in entries[-40:]:
        record = entry.record
        entry_ref = entry.entry_ref
        if entry.entry_kind == "invocation_created":
            _append_timeline_event_once(
                timeline,
                seen,
                record,
                "invocation_requested",
                entry_ref=entry_ref,
                safe_summary="Runtime invocation request was recorded with safe refs only.",
            )
            _append_timeline_event_once(
                timeline,
                seen,
                record,
                "policy_decision",
                entry_ref=entry_ref,
                safe_summary="Runtime policy decision was recorded with blocked authority refs.",
            )
        if record.action_inbox_envelope is not None and entry.entry_kind.startswith(
            "action_inbox_approval_"
        ):
            envelope = record.action_inbox_envelope
            _append_timeline_event_once(
                timeline,
                seen,
                record,
                "approval_requested",
                entry_ref=entry_ref,
                action_envelope_ref=envelope.action_envelope_ref,
                evidence_refs=envelope.evidence_refs,
                safe_summary="Runtime Action Inbox approval envelope was recorded.",
            )
            if envelope.approval_validated:
                _append_timeline_event_once(
                    timeline,
                    seen,
                    record,
                    "approval_accepted",
                    entry_ref=entry_ref,
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary=(
                        "Runtime Action Inbox approval was accepted by backend validation."
                    ),
                )
            elif (
                str(_runtime_value(envelope.status)) == "approval_denied"
                or str(_runtime_value(envelope.decision)) == "deny"
            ):
                _append_timeline_event_once(
                    timeline,
                    seen,
                    record,
                    "approval_denied",
                    entry_ref=entry_ref,
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary="Runtime Action Inbox approval was denied.",
                )
            elif str(_runtime_value(envelope.status)) == "approval_expired":
                _append_timeline_event_once(
                    timeline,
                    seen,
                    record,
                    "approval_expired",
                    entry_ref=entry_ref,
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary="Runtime Action Inbox approval expired before execution.",
                )
        if entry.entry_kind == "action_inbox_execution_started":
            action_envelope_ref = (
                record.action_inbox_envelope.action_envelope_ref
                if record.action_inbox_envelope
                else None
            )
            _append_timeline_event_once(
                timeline,
                seen,
                record,
                "execution_started",
                entry_ref=entry_ref,
                action_envelope_ref=action_envelope_ref,
                safe_summary="Governed runtime command execution started after exact approval.",
            )
        if record.receipt is not None and entry.entry_kind in {
            "receipt_recorded",
            "action_inbox_execution_receipt_linked",
            "execution_blocked_receipt_recorded",
        }:
            _append_receipt_events(timeline, seen, record, entry_ref=entry_ref)
        if entry.entry_kind == "safe_disable_recorded":
            _append_timeline_event_once(
                timeline,
                seen,
                record,
                "safe_disable_invoked",
                entry_ref=entry_ref,
                receipt_ref=record.receipt.receipt_ref if record.receipt else None,
                evidence_refs=[
                    record.safe_disable.safe_disable_ref,
                    record.safe_disable.safe_disable_posture_ref,
                    record.safe_disable.reason_ref,
                ],
                safe_summary="Runtime safe-disable posture was invoked and recorded.",
            )
    return timeline[-40:]


def _evidence_timeline_for_records(
    records: list[RuntimeInvocationRecord],
) -> list[RuntimeActionInboxBridgeEvidenceItem]:
    timeline: list[RuntimeActionInboxBridgeEvidenceItem] = []
    for record in records[-25:]:
        _append_timeline_event(
            timeline,
            record,
            "invocation_requested",
            safe_summary="Runtime invocation request was recorded with safe refs only.",
        )
        _append_timeline_event(
            timeline,
            record,
            "policy_decision",
            safe_summary="Runtime policy decision was recorded with blocked authority refs.",
        )
        if record.action_inbox_envelope is not None:
            envelope = record.action_inbox_envelope
            _append_timeline_event(
                timeline,
                record,
                "approval_requested",
                action_envelope_ref=envelope.action_envelope_ref,
                evidence_refs=envelope.evidence_refs,
                safe_summary="Runtime Action Inbox approval envelope was recorded.",
            )
            if envelope.approval_validated:
                _append_timeline_event(
                    timeline,
                    record,
                    "approval_accepted",
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary="Runtime Action Inbox approval was accepted by backend validation.",
                )
            elif (
                str(_runtime_value(envelope.status)) == "approval_denied"
                or str(_runtime_value(envelope.decision)) == "deny"
            ):
                _append_timeline_event(
                    timeline,
                    record,
                    "approval_denied",
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary="Runtime Action Inbox approval was denied.",
                )
            elif str(_runtime_value(envelope.status)) == "approval_expired":
                _append_timeline_event(
                    timeline,
                    record,
                    "approval_expired",
                    action_envelope_ref=envelope.action_envelope_ref,
                    evidence_refs=envelope.evidence_refs,
                    safe_summary="Runtime Action Inbox approval expired before execution.",
                )
        if record.receipt is not None:
            receipt = record.receipt
            action_envelope_ref = (
                record.action_inbox_envelope.action_envelope_ref
                if record.action_inbox_envelope
                else None
            )
            if (
                receipt.command_receipt_metadata is not None
                and receipt.command_execution_performed
                and receipt.command_receipt_metadata.command_execution_attempted
            ):
                _append_timeline_event(
                    timeline,
                    record,
                    "execution_started",
                    receipt_ref=receipt.receipt_ref,
                    action_envelope_ref=action_envelope_ref,
                    evidence_refs=receipt.evidence_refs,
                    safe_summary="Governed runtime command execution started after exact approval.",
                )
                metadata = receipt.command_receipt_metadata
                if metadata.timed_out:
                    outcome_event = "execution_timed_out"
                    summary = "Governed runtime command execution timed out with redacted output refs."
                elif metadata.exit_code == 0:
                    outcome_event = "execution_completed"
                    summary = "Governed runtime command execution completed with redacted output refs."
                else:
                    outcome_event = "execution_failed"
                    summary = "Governed runtime command execution failed with redacted output refs."
                _append_timeline_event(
                    timeline,
                    record,
                    outcome_event,
                    receipt_ref=receipt.receipt_ref,
                    action_envelope_ref=action_envelope_ref,
                    evidence_refs=receipt.evidence_refs,
                    safe_summary=summary,
                )
            _append_timeline_event(
                timeline,
                record,
                "receipt_recorded",
                receipt_ref=receipt.receipt_ref,
                action_envelope_ref=action_envelope_ref,
                evidence_refs=receipt.evidence_refs,
                safe_summary="Runtime receipt was recorded with redacted evidence refs.",
            )
        if (
            record.safe_disable.active
            and record.safe_disable.reason_ref != DEFAULT_SAFE_DISABLE_REASON_REF
        ):
            _append_timeline_event(
                timeline,
                record,
                "safe_disable_invoked",
                receipt_ref=record.receipt.receipt_ref if record.receipt else None,
                evidence_refs=[
                    record.safe_disable.safe_disable_ref,
                    record.safe_disable.safe_disable_posture_ref,
                    record.safe_disable.reason_ref,
                ],
                safe_summary="Runtime safe-disable posture was invoked and recorded.",
            )
    return timeline[-40:]


def _append_receipt_events(
    timeline: list[RuntimeActionInboxBridgeEvidenceItem],
    seen: set[tuple[str, str]] | None,
    record: RuntimeInvocationRecord,
    *,
    entry_ref: str | None = None,
) -> None:
    if record.receipt is None:
        return
    receipt = record.receipt
    action_envelope_ref = (
        record.action_inbox_envelope.action_envelope_ref
        if record.action_inbox_envelope
        else None
    )
    if (
        receipt.command_receipt_metadata is not None
        and receipt.command_execution_performed
        and receipt.command_receipt_metadata.command_execution_attempted
    ):
        metadata = receipt.command_receipt_metadata
        if metadata.timed_out:
            outcome_event = "execution_timed_out"
            summary = "Governed runtime command execution timed out with redacted output refs."
        elif metadata.exit_code == 0:
            outcome_event = "execution_completed"
            summary = "Governed runtime command execution completed with redacted output refs."
        else:
            outcome_event = "execution_failed"
            summary = "Governed runtime command execution failed with redacted output refs."
        _append_timeline_event_once(
            timeline,
            seen,
            record,
            outcome_event,
            entry_ref=entry_ref,
            receipt_ref=receipt.receipt_ref,
            action_envelope_ref=action_envelope_ref,
            evidence_refs=receipt.evidence_refs,
            safe_summary=summary,
        )
    _append_timeline_event_once(
        timeline,
        seen,
        record,
        "receipt_recorded",
        entry_ref=entry_ref,
        receipt_ref=receipt.receipt_ref,
        action_envelope_ref=action_envelope_ref,
        evidence_refs=receipt.evidence_refs,
        safe_summary="Runtime receipt was recorded with redacted evidence refs.",
    )


def _append_timeline_event_once(
    timeline: list[RuntimeActionInboxBridgeEvidenceItem],
    seen: set[tuple[str, str]] | None,
    record: RuntimeInvocationRecord,
    event_kind: str,
    **kwargs: Any,
) -> None:
    key = (record.invocation_ref, event_kind)
    if seen is not None and key in seen:
        return
    _append_timeline_event(timeline, record, event_kind, **kwargs)
    if seen is not None:
        seen.add(key)


def _append_timeline_event(
    timeline: list[RuntimeActionInboxBridgeEvidenceItem],
    record: RuntimeInvocationRecord,
    event_kind: str,
    *,
    entry_ref: str | None = None,
    receipt_ref: str | None = None,
    action_envelope_ref: str | None = None,
    evidence_refs: list[str] | None = None,
    safe_summary: str,
) -> None:
    timeline.append(
        RuntimeActionInboxBridgeEvidenceItem(
            event_ref=_timeline_event_ref(
                record,
                event_kind,
                entry_ref=entry_ref,
                receipt_ref=receipt_ref,
                action_envelope_ref=action_envelope_ref,
            ),
            event_kind=event_kind,
            invocation_ref=record.invocation_ref,
            receipt_ref=receipt_ref,
            policy_decision_ref=record.policy_decision.policy_decision_ref,
            action_envelope_ref=action_envelope_ref,
            evidence_refs=evidence_refs or [],
            safe_summary=safe_summary,
        )
    )


def _timeline_event_ref(
    record: RuntimeInvocationRecord,
    event_kind: str,
    *,
    entry_ref: str | None = None,
    receipt_ref: str | None = None,
    action_envelope_ref: str | None = None,
) -> str:
    canonical = json.dumps(
        {
            "action_envelope_ref": action_envelope_ref,
            "entry_ref": entry_ref,
            "event_kind": event_kind,
            "invocation_ref": record.invocation_ref,
            "receipt_ref": receipt_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"runtime-event-ref:sha256:{digest}"
