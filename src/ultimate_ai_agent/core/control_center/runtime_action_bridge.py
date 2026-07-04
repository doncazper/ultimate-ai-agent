from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway import RuntimeInvocationRecord


RUNTIME_ACTION_INBOX_BRIDGE_CONTRACT_REF = (
    "contract-ref:governed-runtime-action-inbox-execution-bridge:v1"
)
RUNTIME_ACTION_INBOX_BRIDGE_SOURCE = (
    "python_core_runtime_gateway_action_inbox_bridge_read_model"
)
RUNTIME_ACTION_INBOX_BRIDGE_CLI_REF = (
    "python scripts/dev/uaa_runtime.py inspect-action-inbox-bridge"
)
RUNTIME_ACTION_INBOX_BRIDGE_ROUTE_REF = "GET /control-center/actions/inbox"
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


class RuntimeActionInboxBridgeItem(BaseModel):
    invocation_ref: str = Field(..., min_length=1)
    action_envelope_ref: str = Field(..., min_length=1)
    adapter_id: str = Field(..., min_length=1, max_length=120)
    requested_authority: str = Field(..., min_length=1, max_length=120)
    command_intent: str | None = None
    status: str = Field(..., min_length=1, max_length=120)
    approval_validated: bool = False
    execution_performed: bool = False
    exact_scope_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
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
            (self.idempotency_ref, "idempotency_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.adapter_id, "adapter_id"),
            (self.requested_authority, "requested_authority"),
            (self.command_intent or "not_applicable", "command_intent"),
            (self.status, "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for field_name in (
            "receipt_refs",
            "evidence_refs",
            "blocked_reason_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
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
    status: str = "backend_owned_runtime_action_inbox_bridge"
    item_count: int = Field(ge=0)
    pending_approval_count: int = Field(ge=0)
    approved_pending_execution_count: int = Field(ge=0)
    receipt_recorded_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    item_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    items: list[RuntimeActionInboxBridgeItem] = Field(default_factory=list)
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
            "status",
            "next_safe_action",
            "operator_summary",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in ("item_refs", "receipt_refs", "evidence_refs", "blocked_authority_refs"):
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
) -> dict[str, Any]:
    items = [_item_for_record(record) for record in records if record.action_inbox_envelope]
    receipt_refs = list(dict.fromkeys(ref for item in items for ref in item.receipt_refs))
    evidence_refs = list(dict.fromkeys(ref for item in items for ref in item.evidence_refs))
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
        item_count=len(items),
        pending_approval_count=sum(1 for item in items if item.status == "pending_approval"),
        approved_pending_execution_count=sum(
            1 for item in items if item.status == "approved_pending_execution"
        ),
        receipt_recorded_count=sum(1 for item in items if item.status == "receipt_recorded"),
        blocked_count=blocked_count,
        item_refs=[item.invocation_ref for item in items],
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        items=items,
        blocked_authority_refs=list(RUNTIME_ACTION_INBOX_BRIDGE_BLOCKED_AUTHORITY_REFS),
        operator_summary=(
            f"{len(items)} governed runtime approval envelopes are visible with "
            f"{len(receipt_refs)} receipt refs and {len(evidence_refs)} evidence refs."
        ),
    )
    return model.model_dump(mode="json")


def _item_for_record(record: RuntimeInvocationRecord) -> RuntimeActionInboxBridgeItem:
    envelope = record.action_inbox_envelope
    if envelope is None:  # pragma: no cover - filtered by caller
        raise ValueError("Runtime Action Inbox envelope missing")
    receipt_refs = list(envelope.receipt_refs)
    evidence_refs = list(envelope.evidence_refs)
    if record.receipt is not None:
        receipt_refs = list(dict.fromkeys([*receipt_refs, record.receipt.receipt_ref]))
        evidence_refs = list(dict.fromkeys([*evidence_refs, *record.receipt.evidence_refs]))
    return RuntimeActionInboxBridgeItem(
        invocation_ref=record.invocation_ref,
        action_envelope_ref=envelope.action_envelope_ref,
        adapter_id=envelope.adapter_id,
        requested_authority=str(envelope.requested_authority),
        command_intent=str(envelope.command_intent) if envelope.command_intent else None,
        status=str(record.status),
        approval_validated=bool(envelope.approval_validated),
        execution_performed=bool(record.receipt and record.receipt.execution_performed),
        exact_scope_ref=envelope.exact_scope_ref,
        approval_ref=envelope.approval_ref,
        idempotency_ref=envelope.idempotency_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        payload_fingerprint_ref=record.payload_fingerprint_ref,
        rollback_ref=envelope.rollback_ref,
        safe_disable_ref=envelope.safe_disable_ref,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        blocked_reason_refs=list(envelope.blocked_reason_refs),
        blocked_authority_refs=list(RUNTIME_ACTION_INBOX_BRIDGE_BLOCKED_AUTHORITY_REFS),
        safe_summary=(
            "Exact governed runtime envelope is inspectable through Action Inbox; "
            "broad runtime authority remains blocked."
        ),
    )
