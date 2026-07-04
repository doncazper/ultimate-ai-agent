from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.time import utc_now


GOVERNED_RUNTIME_CONTRACT_REF = "contract-ref:governed-runtime-pilot:v1"
GOVERNED_RUNTIME_DEFAULT_PROFILE = "sealed"
GOVERNED_RUNTIME_CAPABILITIES_REF = "capability-ref:governed-runtime-pilot"
GOVERNED_RUNTIME_SAFE_DISABLE_REF = "safe-disable-ref:governed-runtime-pilot"
GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF = "safe-disable-posture-ref:governed-runtime-pilot"
GOVERNED_RUNTIME_ROLLBACK_REF = "rollback-ref:governed-runtime-pilot:disable-profile"
GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:runtime-adapter-execution-phase-02",
    "blocked-authority:runtime-model-call-phase-02",
    "blocked-authority:runtime-command-execution-phase-02",
    "blocked-authority:runtime-browser-automation",
    "blocked-authority:runtime-connector-write",
    "blocked-authority:runtime-plugin-import",
    "blocked-authority:runtime-remote-execution",
    "blocked-authority:runtime-production-authority",
)
GOVERNED_RUNTIME_REDACTIONS = (
    "safe_refs_only",
    "bounded_summaries_only",
    "prompt_content_omitted",
    "response_content_omitted",
    "command_output_omitted",
    "local_paths_omitted",
    "environment_omitted",
    "sensitive_material_omitted",
)


class RuntimeProfile(str, Enum):
    sealed = "sealed"
    local_runtime = "local-runtime"
    operator_approved = "operator-approved"


class RuntimeAuthority(str, Enum):
    local_model = "local_model"
    allowlisted_command = "allowlisted_command"


class RuntimeInvocationStatus(str, Enum):
    blocked = "blocked"
    pending_approval = "pending_approval"
    approved_pending_execution = "approved_pending_execution"
    execution_blocked = "execution_blocked"
    receipt_recorded = "receipt_recorded"
    safe_disabled = "safe_disabled"


class RuntimeArtifactRef(BaseModel):
    artifact_ref: str = Field(..., min_length=1)
    artifact_kind: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=300)
    safe_refs_only: bool = True
    content_persisted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_artifact(self) -> "RuntimeArtifactRef":
        validate_execution_ref(self.artifact_ref, "artifact_ref")
        validate_safe_execution_text(self.artifact_kind, "artifact_kind")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_ARTIFACT_SAFE_REFS_REQUIRED")
        if self.content_persisted:
            raise ValueError("RUNTIME_ARTIFACT_CONTENT_PERSISTENCE_DENIED")
        return self


class RuntimeRollbackRef(BaseModel):
    rollback_ref: str = GOVERNED_RUNTIME_ROLLBACK_REF
    safe_disable_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_REF
    safe_summary: str = "Runtime pilot rollback is profile downgrade and safe-disable only."
    rollback_available: bool = True
    rollback_executed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_rollback(self) -> "RuntimeRollbackRef":
        validate_execution_ref(self.rollback_ref, "rollback_ref")
        validate_execution_ref(self.safe_disable_ref, "safe_disable_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.rollback_executed:
            raise ValueError("RUNTIME_ROLLBACK_EXECUTION_DENIED_IN_PHASE_02")
        return self


class RuntimeSafeDisableState(BaseModel):
    safe_disable_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_REF
    safe_disable_posture_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF
    active: bool = True
    profile: RuntimeProfile = RuntimeProfile.sealed
    reason_ref: str = "reason-ref:governed-runtime-phase-02-disabled"
    safe_summary: str = "Governed runtime adapters are disabled in Phase 02."
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_safe_disable(self) -> "RuntimeSafeDisableState":
        for value, field_name in [
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
            (self.reason_ref, "reason_ref"),
        ]:
            validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.profile != RuntimeProfile.sealed.value:
            raise ValueError("RUNTIME_SAFE_DISABLE_PROFILE_MUST_BE_SEALED")
        return self


class RuntimeApprovalRequirement(BaseModel):
    approval_required: bool = True
    exact_scope_required: bool = True
    approval_ref: str | None = None
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    action_inbox_envelope_required: bool = True
    approval_validated: bool = False
    approval_binding_recorded: bool = False
    safe_summary: str = "Execution-capable runtime actions require an exact Action Inbox approval envelope."

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_requirement(self) -> "RuntimeApprovalRequirement":
        validate_execution_ref(self.approval_scope_ref, "approval_scope_ref")
        if self.approval_ref:
            validate_execution_ref(self.approval_ref, "approval_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if not self.approval_required or not self.exact_scope_required:
            raise ValueError("RUNTIME_EXACT_APPROVAL_REQUIRED")
        if self.approval_validated and not self.approval_ref:
            raise ValueError("RUNTIME_APPROVAL_REF_REQUIRED")
        return self


class RuntimePolicyDecision(BaseModel):
    policy_decision_ref: str = Field(..., min_length=1)
    profile: RuntimeProfile = RuntimeProfile.sealed
    requested_authority: RuntimeAuthority
    invocation_status: RuntimeInvocationStatus = RuntimeInvocationStatus.blocked
    allowed_to_queue: bool = True
    allowed_to_execute: bool = False
    adapter_execution_enabled: bool = False
    model_call_enabled: bool = False
    command_execution_enabled: bool = False
    approval_requirement: RuntimeApprovalRequirement = Field(
        default_factory=RuntimeApprovalRequirement
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    reason_codes: list[str] = Field(
        default_factory=lambda: [
            "GOVERNED_RUNTIME_PHASE_02_CONTRACT_ONLY",
            "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
        ]
    )
    safe_summary: str = "RuntimeGateway policy recorded a non-executing Phase 02 decision."
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )
    decided_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> "RuntimePolicyDecision":
        validate_execution_ref(self.policy_decision_ref, "policy_decision_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        for reason in self.reason_codes:
            validate_safe_execution_text(reason, "reason_code")
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redaction")
        if self.allowed_to_execute:
            raise ValueError("RUNTIME_EXECUTION_NOT_ALLOWED_IN_PHASE_02")
        if self.adapter_execution_enabled:
            raise ValueError("RUNTIME_ADAPTER_EXECUTION_NOT_ALLOWED_IN_PHASE_02")
        if self.model_call_enabled:
            raise ValueError("RUNTIME_MODEL_CALL_NOT_ALLOWED_IN_PHASE_02")
        if self.command_execution_enabled:
            raise ValueError("RUNTIME_COMMAND_EXECUTION_NOT_ALLOWED_IN_PHASE_02")
        if not set(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS).issubset(
            set(self.blocked_authority_refs)
        ):
            raise ValueError("RUNTIME_BLOCKED_AUTHORITY_REFS_REQUIRED")
        return self


class RuntimeInvocationRequest(BaseModel):
    requested_authority: RuntimeAuthority
    requested_profile: RuntimeProfile = RuntimeProfile.sealed
    input_ref: str = Field(..., min_length=1)
    action_ref: str | None = None
    approval_ref: str | None = None
    idempotency_ref: str | None = None
    safe_summary: str = Field(..., min_length=1, max_length=500)
    artifact_refs: list[RuntimeArtifactRef] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    command_output_persisted: bool = False
    local_path_persisted: bool = False
    environment_persisted: bool = False
    sensitive_material_persisted: bool = False
    provider_exchange_persisted: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "RuntimeInvocationRequest":
        validate_execution_ref(self.input_ref, "input_ref")
        for value, field_name in [
            (self.action_ref, "action_ref"),
            (self.approval_ref, "approval_ref"),
            (self.idempotency_ref, "idempotency_ref"),
        ]:
            if value:
                validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_INVOCATION_SAFE_REFS_REQUIRED")
        unsafe_flags = {
            "prompt_content_persisted": self.prompt_content_persisted,
            "response_content_persisted": self.response_content_persisted,
            "command_output_persisted": self.command_output_persisted,
            "local_path_persisted": self.local_path_persisted,
            "environment_persisted": self.environment_persisted,
            "sensitive_material_persisted": self.sensitive_material_persisted,
            "provider_exchange_persisted": self.provider_exchange_persisted,
        }
        if any(unsafe_flags.values()):
            raise ValueError("RUNTIME_INVOCATION_UNSAFE_PERSISTENCE_DENIED")
        return self


class RuntimeInvocationReceipt(BaseModel):
    receipt_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    invocation_status: RuntimeInvocationStatus = RuntimeInvocationStatus.execution_blocked
    artifact_refs: list[RuntimeArtifactRef] = Field(default_factory=list)
    rollback: RuntimeRollbackRef = Field(default_factory=RuntimeRollbackRef)
    safe_disable: RuntimeSafeDisableState = Field(default_factory=RuntimeSafeDisableState)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )
    execution_performed: bool = False
    adapter_execution_performed: bool = False
    model_call_performed: bool = False
    command_execution_performed: bool = False
    connector_write_performed: bool = False
    browser_automation_performed: bool = False
    safe_summary: str = "Runtime invocation receipt recorded a blocked Phase 02 execution attempt."
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "RuntimeInvocationReceipt":
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for ref in self.evidence_refs:
            validate_execution_ref(ref, "evidence_ref")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redaction")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if any(
            [
                self.execution_performed,
                self.adapter_execution_performed,
                self.model_call_performed,
                self.command_execution_performed,
                self.connector_write_performed,
                self.browser_automation_performed,
            ]
        ):
            raise ValueError("RUNTIME_RECEIPT_EXECUTION_DENIED_IN_PHASE_02")
        return self


class RuntimeApprovalBindingRequest(BaseModel):
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    safe_summary: str = "Approval binding recorded as an identifier only."
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding_request(self) -> "RuntimeApprovalBindingRequest":
        validate_execution_ref(self.approval_ref, "approval_ref")
        validate_execution_ref(self.approval_scope_ref, "approval_scope_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        return self


class RuntimeExecuteRequest(BaseModel):
    approval_ref: str | None = None
    safe_summary: str = "Execute request records a blocked Phase 02 receipt only."
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_execute_request(self) -> "RuntimeExecuteRequest":
        if self.approval_ref:
            validate_execution_ref(self.approval_ref, "approval_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        return self


class RuntimeSafeDisableRequest(BaseModel):
    reason_ref: str = "reason-ref:governed-runtime-safe-disable-request"
    safe_summary: str = "Operator requested governed runtime safe-disable posture."
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_safe_disable_request(self) -> "RuntimeSafeDisableRequest":
        validate_execution_ref(self.reason_ref, "reason_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        return self


class RuntimeInvocationRecord(BaseModel):
    invocation_ref: str = Field(..., min_length=1)
    request: RuntimeInvocationRequest
    policy_decision: RuntimePolicyDecision
    approval_requirement: RuntimeApprovalRequirement
    receipt: RuntimeInvocationReceipt | None = None
    payload_fingerprint_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    safe_disable: RuntimeSafeDisableState = Field(default_factory=RuntimeSafeDisableState)
    status: RuntimeInvocationStatus = RuntimeInvocationStatus.blocked
    replay_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeInvocationRecord":
        for value, field_name in [
            (self.invocation_ref, "invocation_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.idempotency_ref, "idempotency_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.receipt and self.receipt.invocation_ref != self.invocation_ref:
            raise ValueError("RUNTIME_RECEIPT_INVOCATION_REF_MISMATCH")
        return self


class RuntimeCapabilities(BaseModel):
    schema_version: str = "governed_runtime_capabilities.v1"
    contract_ref: str = GOVERNED_RUNTIME_CONTRACT_REF
    capabilities_ref: str = GOVERNED_RUNTIME_CAPABILITIES_REF
    default_profile: RuntimeProfile = RuntimeProfile.sealed
    supported_profiles: list[RuntimeProfile] = Field(
        default_factory=lambda: [
            RuntimeProfile.sealed,
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        ]
    )
    supported_authorities: list[RuntimeAuthority] = Field(
        default_factory=lambda: [
            RuntimeAuthority.local_model,
            RuntimeAuthority.allowlisted_command,
        ]
    )
    adapter_execution_enabled: bool = False
    model_call_enabled: bool = False
    command_execution_enabled: bool = False
    approval_required_for_execution: bool = True
    safe_disable: RuntimeSafeDisableState = Field(default_factory=RuntimeSafeDisableState)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_capabilities(self) -> "RuntimeCapabilities":
        validate_execution_ref(self.contract_ref, "contract_ref")
        validate_execution_ref(self.capabilities_ref, "capabilities_ref")
        if self.default_profile != RuntimeProfile.sealed.value:
            raise ValueError("RUNTIME_DEFAULT_PROFILE_MUST_BE_SEALED")
        if self.adapter_execution_enabled or self.model_call_enabled or self.command_execution_enabled:
            raise ValueError("RUNTIME_CAPABILITY_EXECUTION_DENIED_IN_PHASE_02")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        return self


def _stable_ref(prefix: str, payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"


def runtime_payload_fingerprint_ref(request: RuntimeInvocationRequest) -> str:
    payload = request.model_dump(mode="json", exclude={"idempotency_ref"})
    validate_safe_execution_payload(payload, "runtime_invocation_request")
    return _stable_ref("runtime-payload-fingerprint-ref", payload)


def runtime_invocation_ref(idempotency_ref: str, payload_fingerprint_ref: str) -> str:
    validate_execution_ref(idempotency_ref, "idempotency_ref")
    validate_execution_ref(payload_fingerprint_ref, "payload_fingerprint_ref")
    return _stable_ref(
        "runtime-invocation-ref",
        {"idempotency_ref": idempotency_ref, "payload": payload_fingerprint_ref},
    )


def runtime_policy_decision_ref(invocation_ref: str) -> str:
    validate_execution_ref(invocation_ref, "invocation_ref")
    return _stable_ref("runtime-policy-decision-ref", {"invocation_ref": invocation_ref})


def runtime_receipt_ref(invocation_ref: str, status: RuntimeInvocationStatus) -> str:
    validate_execution_ref(invocation_ref, "invocation_ref")
    return _stable_ref(
        "runtime-receipt-ref",
        {"invocation_ref": invocation_ref, "status": str(status.value)},
    )


def build_policy_decision(
    request: RuntimeInvocationRequest,
    *,
    invocation_ref: str,
    approval_ref: str | None = None,
    status: RuntimeInvocationStatus = RuntimeInvocationStatus.blocked,
) -> RuntimePolicyDecision:
    approval_requirement = RuntimeApprovalRequirement(
        approval_ref=approval_ref or request.approval_ref,
        approval_validated=False,
        approval_binding_recorded=bool(approval_ref or request.approval_ref),
    )
    reason_codes = [
        "GOVERNED_RUNTIME_PHASE_02_CONTRACT_ONLY",
        "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
    ]
    if approval_ref or request.approval_ref:
        reason_codes.append("APPROVAL_REF_IDENTIFIER_ONLY")
    return RuntimePolicyDecision(
        policy_decision_ref=runtime_policy_decision_ref(invocation_ref),
        profile=RuntimeProfile.sealed,
        requested_authority=request.requested_authority,
        invocation_status=status,
        approval_requirement=approval_requirement,
        reason_codes=reason_codes,
    )


def build_blocked_receipt(
    record: RuntimeInvocationRecord,
    *,
    safe_summary: str = "Runtime execution remains blocked in Phase 02.",
) -> RuntimeInvocationReceipt:
    return RuntimeInvocationReceipt(
        receipt_ref=runtime_receipt_ref(
            record.invocation_ref,
            RuntimeInvocationStatus.execution_blocked,
        ),
        invocation_ref=record.invocation_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        artifact_refs=[
            RuntimeArtifactRef(
                artifact_ref=_stable_ref(
                    "runtime-artifact-ref",
                    {"invocation_ref": record.invocation_ref, "kind": "blocked-receipt"},
                ),
                artifact_kind="blocked_runtime_receipt",
                safe_summary="Blocked runtime receipt stores safe refs only.",
            )
        ],
        evidence_refs=[
            _stable_ref(
                "runtime-evidence-ref",
                {"invocation_ref": record.invocation_ref, "status": "blocked"},
            )
        ],
        safe_summary=safe_summary,
    )


def build_default_runtime_capabilities() -> RuntimeCapabilities:
    return RuntimeCapabilities()
