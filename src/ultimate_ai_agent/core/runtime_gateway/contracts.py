from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityDecisionOutcome,
    AuthorityDomain,
    AuthorityLease,
    TrustMode,
    evaluate_authority_request,
)
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
GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF = (
    "safe-disable-posture-ref:governed-runtime-pilot"
)
GOVERNED_RUNTIME_ROLLBACK_REF = "rollback-ref:governed-runtime-pilot:disable-profile"
GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS = (
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
GOVERNED_RUNTIME_IMPLEMENTED_AUTHORITY_REFS = (
    "authority-ref:runtime-local-model-loopback-phase-03",
    "authority-ref:runtime-allowlisted-readonly-command-phase-04",
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
MAX_RUNTIME_RECEIPT_EVIDENCE_REFS = 32
MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS = 32
MAX_RUNTIME_GOAL_VERSION = 4096
MAX_RUNTIME_EXECUTION_REF_LENGTH = 320


class RuntimeProfile(str, Enum):
    sealed = "sealed"
    local_runtime = "local-runtime"
    operator_approved = "operator-approved"


class RuntimeAuthority(str, Enum):
    local_model = "local_model"
    allowlisted_command = "allowlisted_command"


class RuntimeCommandIntent(str, Enum):
    git_status = "git_status"
    focused_pytest = "focused_pytest"
    repo_verifier = "repo_verifier"
    frontend_check = "frontend_check"
    repo_doctor = "repo_doctor"


class RuntimeInvocationStatus(str, Enum):
    blocked = "blocked"
    pending_approval = "pending_approval"
    approved_pending_execution = "approved_pending_execution"
    approval_denied = "approval_denied"
    approval_expired = "approval_expired"
    execution_blocked = "execution_blocked"
    receipt_recorded = "receipt_recorded"
    safe_disabled = "safe_disabled"


class RuntimeActionInboxApprovalDecision(str, Enum):
    approve = "approve"
    deny = "deny"
    expire = "expire"


class RuntimeActionInboxApprovalEnvelope(BaseModel):
    schema_version: str = "governed_runtime_action_inbox_approval_envelope.v1"
    action_envelope_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    adapter_id: str = Field(..., min_length=1, max_length=120)
    requested_authority: RuntimeAuthority
    command_intent: RuntimeCommandIntent | None = None
    exact_scope_ref: str = Field(..., min_length=1)
    payload_fingerprint_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    approval_decision_ref: str | None = None
    approval_validation_ref: str | None = None
    approval_ref_is_identifier_only: bool = True
    risk_class: Literal["safe", "low", "medium", "high", "critical"] = "medium"
    expires_at: datetime = Field(
        default_factory=lambda: utc_now() + timedelta(minutes=30)
    )
    decision: RuntimeActionInboxApprovalDecision = (
        RuntimeActionInboxApprovalDecision.approve
    )
    status: RuntimeInvocationStatus = RuntimeInvocationStatus.pending_approval
    idempotency_ref: str = Field(..., min_length=1)
    rollback_ref: str = GOVERNED_RUNTIME_ROLLBACK_REF
    safe_disable_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_REF
    safe_disable_posture_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF
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
    stale_policy: bool = False
    scope_mismatch: bool = False
    runtime_profile_weaker_or_disabled: bool = False
    safe_disable_active: bool = False
    blocked_reason_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Action Inbox runtime approval envelope stores exact safe refs only."
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_action_inbox_envelope(self) -> "RuntimeActionInboxApprovalEnvelope":
        for value, field_name in [
            (self.action_envelope_ref, "action_envelope_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.payload_fingerprint_ref, "payload_fingerprint_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.approval_ref, "approval_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.approval_decision_ref, "approval_decision_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.idempotency_ref, "idempotency_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
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
            (self.schema_version, "schema_version"),
            (self.adapter_id, "adapter_id"),
            (self.risk_class, "risk_class"),
            (
                self.authority_decision_outcome or "authority-decision-outcome:none",
                "authority_decision_outcome",
            ),
            (
                self.authority_operator_message or "authority-message:none",
                "authority_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for field_name in (
            "authority_reason_refs",
            "blocked_reason_refs",
            "evidence_refs",
            "receipt_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        if (
            self.command_intent is None
            and self.requested_authority == RuntimeAuthority.allowlisted_command.value
        ):
            raise ValueError("RUNTIME_ACTION_INBOX_COMMAND_INTENT_REQUIRED")
        if (
            self.approval_validated
            and self.decision != RuntimeActionInboxApprovalDecision.approve.value
        ):
            raise ValueError("RUNTIME_ACTION_INBOX_APPROVED_DECISION_REQUIRED")
        if (
            self.execution_performed
            and self.status != RuntimeInvocationStatus.receipt_recorded.value
        ):
            raise ValueError("RUNTIME_ACTION_INBOX_EXECUTION_STATUS_REQUIRED")
        return self


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
    safe_summary: str = (
        "Runtime pilot rollback is profile downgrade and safe-disable only."
    )
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
    safe_summary: str = "Governed runtime is sealed by default; Phase 03 local loopback model calls require explicit local enablement."
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
        if self.active and self.profile != RuntimeProfile.sealed.value:
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
    authority_decision_ref: str | None = None
    authority_decision_outcome: str | None = None
    authority_lease_ref: str | None = None
    authority_domain: str | None = None
    authority_capability: str | None = None
    authority_required_mode: str | None = None
    authority_reason_refs: list[str] = Field(default_factory=list)
    authority_audit_ref: str | None = None
    authority_policy_receipt_ref: str | None = None
    authority_rollback_ref: str | None = None
    authority_safe_disable_ref: str | None = None
    authority_known_authority: bool | None = None
    authority_unsupported_adapter: bool | None = None
    authority_operator_message: str | None = None
    safe_summary: str = "RuntimeGateway policy recorded a governed runtime decision."
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
        for value, field_name in [
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.authority_lease_ref, "authority_lease_ref"),
            (self.authority_audit_ref, "authority_audit_ref"),
            (self.authority_policy_receipt_ref, "authority_policy_receipt_ref"),
            (self.authority_rollback_ref, "authority_rollback_ref"),
            (self.authority_safe_disable_ref, "authority_safe_disable_ref"),
        ]:
            if value:
                validate_execution_ref(value, field_name)
        for ref in self.authority_reason_refs:
            validate_execution_ref(ref, "authority_reason_ref")
        for value, field_name in [
            (self.authority_decision_outcome, "authority_decision_outcome"),
            (self.authority_domain, "authority_domain"),
            (self.authority_capability, "authority_capability"),
            (self.authority_required_mode, "authority_required_mode"),
            (self.authority_operator_message, "authority_operator_message"),
        ]:
            if value:
                validate_safe_execution_text(value, field_name)
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redaction")
        if self.allowed_to_execute:
            if self.profile not in {
                RuntimeProfile.local_runtime.value,
                RuntimeProfile.operator_approved.value,
            }:
                raise ValueError("RUNTIME_EXECUTION_PROFILE_NOT_PROMOTED")
            if self.requested_authority == RuntimeAuthority.local_model.value:
                if (
                    not self.adapter_execution_enabled
                    or not self.model_call_enabled
                    or self.command_execution_enabled
                ):
                    raise ValueError("RUNTIME_LOCAL_MODEL_EXECUTION_FLAGS_REQUIRED")
            elif self.requested_authority == RuntimeAuthority.allowlisted_command.value:
                if (
                    not self.adapter_execution_enabled
                    or not self.command_execution_enabled
                    or self.model_call_enabled
                ):
                    raise ValueError("RUNTIME_COMMAND_EXECUTION_FLAGS_REQUIRED")
            else:
                raise ValueError("RUNTIME_EXECUTION_AUTHORITY_NOT_PROMOTED")
        elif (
            self.adapter_execution_enabled
            or self.model_call_enabled
            or self.command_execution_enabled
        ):
            raise ValueError("RUNTIME_EXECUTION_FLAGS_REQUIRE_ALLOW")
        if self.model_call_enabled and self.command_execution_enabled:
            raise ValueError("RUNTIME_SINGLE_EXECUTION_AUTHORITY_REQUIRED")
        if self.model_call_enabled:
            if self.requested_authority != RuntimeAuthority.local_model.value:
                raise ValueError("RUNTIME_LOCAL_MODEL_EXECUTION_FLAGS_REQUIRED")
        if self.command_execution_enabled:
            if self.requested_authority != RuntimeAuthority.allowlisted_command.value:
                raise ValueError("RUNTIME_COMMAND_EXECUTION_FLAGS_REQUIRED")
        if not set(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS).issubset(
            set(self.blocked_authority_refs)
        ):
            raise ValueError("RUNTIME_BLOCKED_AUTHORITY_REFS_REQUIRED")
        return self


class RuntimeInvocationRequest(BaseModel):
    requested_authority: RuntimeAuthority
    requested_profile: RuntimeProfile = RuntimeProfile.sealed
    input_ref: str = Field(..., min_length=1)
    mission_ref: str | None = None
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
            (self.mission_ref, "mission_ref"),
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


class RuntimeCriterionVerificationBinding(BaseModel):
    """Trusted evaluator provenance for one exact goal success criterion."""

    goal_ref: str = Field(..., min_length=1)
    goal_version: StrictInt = Field(..., ge=1, le=MAX_RUNTIME_GOAL_VERSION)
    criterion_ref: str = Field(..., min_length=1)
    proof_ref: str = Field(..., min_length=1)
    verifier_ref: str = Field(..., min_length=1)
    evaluator_receipt_ref: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "RuntimeCriterionVerificationBinding":
        for value, field_name in (
            (self.goal_ref, "goal_ref"),
            (self.criterion_ref, "criterion_ref"),
            (self.proof_ref, "proof_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.evaluator_receipt_ref, "evaluator_receipt_ref"),
        ):
            if len(value) > MAX_RUNTIME_EXECUTION_REF_LENGTH:
                raise ValueError(f"{field_name} exceeds the bounded ref length")
            validate_execution_ref(value, field_name)
        return self


class RuntimeInvocationReceipt(BaseModel):
    receipt_ref: str = Field(..., min_length=1)
    invocation_ref: str = Field(..., min_length=1)
    policy_decision_ref: str = Field(..., min_length=1)
    invocation_status: RuntimeInvocationStatus = (
        RuntimeInvocationStatus.execution_blocked
    )
    artifact_refs: list[RuntimeArtifactRef] = Field(default_factory=list)
    rollback: RuntimeRollbackRef = Field(default_factory=RuntimeRollbackRef)
    safe_disable: RuntimeSafeDisableState = Field(
        default_factory=RuntimeSafeDisableState
    )
    evidence_refs: list[str] = Field(
        default_factory=list,
        max_length=MAX_RUNTIME_RECEIPT_EVIDENCE_REFS,
    )
    criterion_verification_bindings: list[RuntimeCriterionVerificationBinding] = Field(
        default_factory=list,
        max_length=MAX_RUNTIME_CRITERION_VERIFICATION_BINDINGS,
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
    )
    model_receipt_metadata: "RuntimeLocalModelReceiptMetadata | None" = None
    command_receipt_metadata: "RuntimeCommandReceiptMetadata | None" = None
    execution_performed: bool = False
    adapter_execution_performed: bool = False
    model_call_performed: bool = False
    command_execution_performed: bool = False
    connector_write_performed: bool = False
    browser_automation_performed: bool = False
    model_output_non_authoritative: bool = True
    safe_summary: str = (
        "Runtime invocation receipt recorded a governed runtime attempt."
    )
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "RuntimeInvocationReceipt":
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.invocation_ref, "invocation_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
        ]:
            if len(value) > MAX_RUNTIME_EXECUTION_REF_LENGTH:
                raise ValueError(f"{field_name} exceeds the bounded ref length")
            validate_execution_ref(value, field_name)
        for ref in self.evidence_refs:
            if len(ref) > MAX_RUNTIME_EXECUTION_REF_LENGTH:
                raise ValueError("evidence_ref exceeds the bounded ref length")
            validate_execution_ref(ref, "evidence_ref")
        binding_keys = {
            (
                binding.goal_ref,
                binding.goal_version,
                binding.criterion_ref,
            )
            for binding in self.criterion_verification_bindings
        }
        if len(binding_keys) != len(self.criterion_verification_bindings):
            raise ValueError("RUNTIME_CRITERION_VERIFICATION_BINDING_DUPLICATE")
        if (
            self.criterion_verification_bindings
            and self.invocation_status != RuntimeInvocationStatus.receipt_recorded.value
        ):
            raise ValueError("RUNTIME_CRITERION_VERIFICATION_TERMINAL_RECEIPT_REQUIRED")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redaction")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.model_receipt_metadata is not None:
            if self.connector_write_performed or self.browser_automation_performed:
                raise ValueError("RUNTIME_NON_MODEL_AUTHORITY_NOT_ALLOWED")
            if self.command_execution_performed:
                raise ValueError(
                    "RUNTIME_COMMAND_AND_MODEL_EXECUTION_MUTUALLY_EXCLUSIVE"
                )
            if not self.model_output_non_authoritative:
                raise ValueError("RUNTIME_MODEL_OUTPUT_NON_AUTHORITATIVE_REQUIRED")
            if self.command_receipt_metadata is not None:
                raise ValueError(
                    "RUNTIME_COMMAND_AND_MODEL_METADATA_MUTUALLY_EXCLUSIVE"
                )
            if self.model_receipt_metadata.attempt_outcome_unknown and any(
                (
                    self.execution_performed,
                    self.adapter_execution_performed,
                    self.model_call_performed,
                )
            ):
                raise ValueError(
                    "RUNTIME_MODEL_ATTEMPT_OUTCOME_UNKNOWN_EXECUTION_INVALID"
                )
        if self.command_receipt_metadata is not None:
            if (
                self.connector_write_performed
                or self.browser_automation_performed
                or self.model_call_performed
            ):
                raise ValueError("RUNTIME_NON_COMMAND_AUTHORITY_NOT_ALLOWED")
            if self.command_execution_performed:
                if not self.execution_performed or not self.adapter_execution_performed:
                    raise ValueError("RUNTIME_COMMAND_RECEIPT_EXECUTION_FLAGS_REQUIRED")
                if not self.command_receipt_metadata.command_execution_attempted:
                    raise ValueError("RUNTIME_COMMAND_METADATA_ATTEMPT_REQUIRED")
            return self
        if self.model_call_performed:
            if not self.execution_performed or not self.adapter_execution_performed:
                raise ValueError("RUNTIME_MODEL_RECEIPT_EXECUTION_FLAGS_REQUIRED")
            if self.model_receipt_metadata is None:
                raise ValueError("RUNTIME_MODEL_RECEIPT_METADATA_REQUIRED")
            return self
        if any(
            [
                self.execution_performed,
                self.adapter_execution_performed,
                self.command_execution_performed,
                self.connector_write_performed,
                self.browser_automation_performed,
            ]
        ):
            raise ValueError(
                "RUNTIME_RECEIPT_EXECUTION_DENIED_WITHOUT_AUTHORITY_LEASE_CAPABILITY"
            )
        return self


class RuntimeCommandAllowlistEntry(BaseModel):
    intent: RuntimeCommandIntent
    command_shape_ref: str = Field(..., min_length=1)
    enabled_for_phase: bool = False
    no_op_readonly: bool = False
    approval_required: bool = True
    exact_action_inbox_approval_required: bool = True
    network_access_allowed: bool = False
    command_output_persisted: bool = False
    safe_summary: str = Field(..., min_length=1, max_length=300)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_allowlist_entry(self) -> "RuntimeCommandAllowlistEntry":
        validate_execution_ref(self.command_shape_ref, "command_shape_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.enabled_for_phase and self.approval_required and self.no_op_readonly:
            raise ValueError("RUNTIME_COMMAND_NO_OP_APPROVAL_POSTURE_CONFLICT")
        if self.network_access_allowed:
            raise ValueError("RUNTIME_COMMAND_NETWORK_ACCESS_DENIED")
        if self.command_output_persisted:
            raise ValueError("RUNTIME_COMMAND_RAW_OUTPUT_PERSISTENCE_DENIED")
        if self.enabled_for_phase and not self.no_op_readonly:
            raise ValueError("RUNTIME_COMMAND_PHASE_04_ONLY_NO_OP_STATUS_ENABLED")
        return self


class RuntimeCommandReceiptMetadata(BaseModel):
    adapter_id: str = "governed-command-runtime-adapter"
    intent: RuntimeCommandIntent
    command_shape_ref: str = Field(..., min_length=1)
    argv_ref: str = Field(..., min_length=1)
    cwd_ref: str = Field(..., min_length=1)
    environment_ref: str = Field(..., min_length=1)
    profile: RuntimeProfile = RuntimeProfile.local_runtime
    exit_code: int | None = None
    timed_out: bool = False
    duration_ms: int = Field(default=0, ge=0, le=300_000)
    output_byte_count: int = Field(default=0, ge=0, le=1_000_000)
    output_truncated: bool = False
    redacted_output_ref: str = Field(..., min_length=1)
    output_summary: str = Field(..., min_length=1, max_length=300)
    status_category: str = Field(..., min_length=1, max_length=120)
    error_category: str | None = None
    command_execution_attempted: bool = False
    shell_used: bool = False
    command_string_accepted: bool = False
    network_access_allowed: bool = False
    command_output_persisted: bool = False
    cwd_persisted: bool = False
    environment_persisted: bool = False
    safe_summary: str = "Command runtime metadata stores safe refs, counts, and redacted summaries only."

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_command_metadata(self) -> "RuntimeCommandReceiptMetadata":
        for value, field_name in [
            (self.adapter_id, "adapter_id"),
            (self.status_category, "status_category"),
            (self.output_summary, "output_summary"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for value, field_name in [
            (self.command_shape_ref, "command_shape_ref"),
            (self.argv_ref, "argv_ref"),
            (self.cwd_ref, "cwd_ref"),
            (self.environment_ref, "environment_ref"),
            (self.redacted_output_ref, "redacted_output_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.profile not in {
            RuntimeProfile.local_runtime.value,
            RuntimeProfile.operator_approved.value,
        }:
            raise ValueError("RUNTIME_COMMAND_PROFILE_REQUIRED")
        if self.shell_used or self.command_string_accepted:
            raise ValueError("RUNTIME_COMMAND_SHELL_OR_STRING_DENIED")
        if self.network_access_allowed:
            raise ValueError("RUNTIME_COMMAND_NETWORK_ACCESS_DENIED")
        if self.command_output_persisted:
            raise ValueError("RUNTIME_COMMAND_RAW_OUTPUT_PERSISTENCE_DENIED")
        if self.cwd_persisted:
            raise ValueError("RUNTIME_COMMAND_CWD_PERSISTENCE_DENIED")
        if self.environment_persisted:
            raise ValueError("RUNTIME_COMMAND_ENV_PERSISTENCE_DENIED")
        if self.error_category:
            validate_safe_execution_text(self.error_category, "error_category")
        return self


class RuntimeLocalModelReceiptMetadata(BaseModel):
    adapter_id: str = "local-model-runtime-adapter"
    model_ref: str = Field(..., min_length=1)
    endpoint_ref: str = Field(..., min_length=1)
    profile: RuntimeProfile = RuntimeProfile.local_runtime
    request_byte_count: int = Field(default=0, ge=0, le=1_000_000)
    response_byte_count: int = Field(default=0, ge=0, le=1_000_000)
    status_code: int | None = Field(default=None, ge=100, le=599)
    response_received: bool = False
    response_truncated: bool = False
    bounded_preview_returned: bool = False
    bounded_preview_persisted: bool = False
    error_category: str | None = None
    attempt_outcome_unknown: bool = False
    model_output_non_authoritative: bool = True
    tools_executed: bool = False
    memory_written: bool = False
    files_written: bool = False
    provider_called: bool = False
    remote_called: bool = False
    safe_summary: str = "Local model runtime metadata stores safe refs and counts only."

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_local_model_metadata(self) -> "RuntimeLocalModelReceiptMetadata":
        validate_safe_execution_text(self.adapter_id, "adapter_id")
        validate_safe_execution_text(self.model_ref, "model_ref")
        validate_execution_ref(self.endpoint_ref, "endpoint_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.profile not in {
            RuntimeProfile.local_runtime.value,
            RuntimeProfile.operator_approved.value,
        }:
            raise ValueError("RUNTIME_LOCAL_MODEL_PROFILE_REQUIRED")
        if self.bounded_preview_persisted:
            raise ValueError("RUNTIME_MODEL_PREVIEW_PERSISTENCE_NOT_ENABLED")
        if not self.model_output_non_authoritative:
            raise ValueError("RUNTIME_MODEL_OUTPUT_NON_AUTHORITATIVE_REQUIRED")
        if any(
            [
                self.tools_executed,
                self.memory_written,
                self.files_written,
                self.provider_called,
                self.remote_called,
            ]
        ):
            raise ValueError("RUNTIME_MODEL_SIDE_EFFECT_DENIED")
        if self.error_category:
            validate_safe_execution_text(self.error_category, "error_category")
        if (
            self.attempt_outcome_unknown
            != (self.error_category == "RUNTIME_LOCAL_MODEL_ATTEMPT_OUTCOME_UNKNOWN")
            or self.attempt_outcome_unknown
            and (
                self.status_code is not None
                or self.response_received
                or self.response_byte_count != 0
                or self.response_truncated
                or self.bounded_preview_returned
            )
        ):
            raise ValueError("RUNTIME_MODEL_ATTEMPT_OUTCOME_UNKNOWN_INVALID")
        return self


class RuntimeApprovalBindingRequest(BaseModel):
    approval_ref: str | None = Field(default=None, min_length=1)
    approval_scope_ref: str = "approval-scope-ref:governed-runtime-exact-envelope"
    decision: RuntimeActionInboxApprovalDecision = (
        RuntimeActionInboxApprovalDecision.approve
    )
    action_envelope_ref: str | None = None
    exact_scope_ref: str | None = None
    expected_payload_fingerprint_ref: str | None = None
    expected_policy_decision_ref: str | None = None
    adapter_id: str | None = None
    command_intent: RuntimeCommandIntent | None = None
    risk_class: Literal["safe", "low", "medium", "high", "critical"] = "medium"
    expires_at: datetime | None = None
    rollback_ref: str = GOVERNED_RUNTIME_ROLLBACK_REF
    safe_disable_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_REF
    safe_disable_posture_ref: str = GOVERNED_RUNTIME_SAFE_DISABLE_POSTURE_REF
    safe_summary: str = "Approval binding recorded as an identifier only."
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding_request(self) -> "RuntimeApprovalBindingRequest":
        if self.approval_ref is not None:
            validate_execution_ref(self.approval_ref, "approval_ref")
        validate_execution_ref(self.approval_scope_ref, "approval_scope_ref")
        for value, field_name in [
            (self.action_envelope_ref, "action_envelope_ref"),
            (self.exact_scope_ref, "exact_scope_ref"),
            (self.expected_payload_fingerprint_ref, "expected_payload_fingerprint_ref"),
            (self.expected_policy_decision_ref, "expected_policy_decision_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.safe_disable_posture_ref, "safe_disable_posture_ref"),
        ]:
            if value:
                validate_execution_ref(value, field_name)
        if self.adapter_id:
            validate_safe_execution_text(self.adapter_id, "adapter_id")
        validate_safe_execution_text(self.risk_class, "risk_class")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        return self


class RuntimeExecuteRequest(BaseModel):
    approval_ref: str | None = None
    action_envelope_ref: str | None = None
    expected_payload_fingerprint_ref: str | None = None
    expected_policy_decision_ref: str | None = None
    command_request: dict[str, Any] | None = None
    safe_summary: str = (
        "Execute request records a blocked receipt until an active "
        "AuthorityLease capability and approval binding allow execution."
    )
    metadata_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_execute_request(self) -> "RuntimeExecuteRequest":
        for value, field_name in [
            (self.approval_ref, "approval_ref"),
            (self.action_envelope_ref, "action_envelope_ref"),
            (self.expected_payload_fingerprint_ref, "expected_payload_fingerprint_ref"),
            (self.expected_policy_decision_ref, "expected_policy_decision_ref"),
        ]:
            if value:
                validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        if self.command_request is not None:
            validate_safe_execution_payload(self.command_request, "command_request")
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
    action_inbox_envelope: RuntimeActionInboxApprovalEnvelope | None = None
    receipt: RuntimeInvocationReceipt | None = None
    payload_fingerprint_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    adapter_dispatch_protocol_ref: str | None = None
    adapter_dispatch_started: bool = False
    safe_disable: RuntimeSafeDisableState = Field(
        default_factory=RuntimeSafeDisableState
    )
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
        if self.adapter_dispatch_protocol_ref is not None:
            validate_execution_ref(
                self.adapter_dispatch_protocol_ref,
                "adapter_dispatch_protocol_ref",
            )
        if (
            self.adapter_dispatch_started
            and self.adapter_dispatch_protocol_ref is None
        ):
            raise ValueError("RUNTIME_ADAPTER_DISPATCH_PROTOCOL_REQUIRED")
        if self.receipt and self.receipt.invocation_ref != self.invocation_ref:
            raise ValueError("RUNTIME_RECEIPT_INVOCATION_REF_MISMATCH")
        if self.receipt and self.receipt.criterion_verification_bindings:
            if self.request.mission_ref is None or any(
                binding.goal_ref != self.request.mission_ref
                for binding in self.receipt.criterion_verification_bindings
            ):
                raise ValueError("RUNTIME_CRITERION_VERIFICATION_GOAL_BINDING_MISMATCH")
        return self


def runtime_invocation_has_committed_receipt(
    record: RuntimeInvocationRecord,
) -> bool:
    """Derive commitment from immutable terminal receipt evidence."""

    receipt = record.receipt
    return bool(
        receipt is not None
        and receipt.invocation_status == RuntimeInvocationStatus.receipt_recorded.value
        and record.status
        in {
            RuntimeInvocationStatus.receipt_recorded.value,
            RuntimeInvocationStatus.safe_disabled.value,
        }
    )


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
    safe_disable: RuntimeSafeDisableState = Field(
        default_factory=RuntimeSafeDisableState
    )
    implemented_authority_refs: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_IMPLEMENTED_AUTHORITY_REFS)
    )
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
        if self.model_call_enabled and self.command_execution_enabled:
            raise ValueError("RUNTIME_SINGLE_EXECUTION_CAPABILITY_REQUIRED")
        if self.adapter_execution_enabled and not (
            self.model_call_enabled or self.command_execution_enabled
        ):
            raise ValueError("RUNTIME_ADAPTER_FLAG_REQUIRES_EXECUTION_CAPABILITY")
        if self.adapter_execution_enabled and self.safe_disable.active:
            raise ValueError("RUNTIME_CAPABILITY_SAFE_DISABLE_MUST_BE_INACTIVE")
        for ref in self.implemented_authority_refs:
            validate_execution_ref(ref, "implemented_authority_ref")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_ref")
        return self


def _stable_ref(prefix: str, payload: Any) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return (
        f"{prefix}:sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:24]}"
    )


def runtime_payload_fingerprint_ref(request: RuntimeInvocationRequest) -> str:
    excluded_fields = {"idempotency_ref"}
    if request.mission_ref is None:
        excluded_fields.add("mission_ref")
    payload = request.model_dump(mode="json", exclude=excluded_fields)
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
    return _stable_ref(
        "runtime-policy-decision-ref", {"invocation_ref": invocation_ref}
    )


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
    local_model_gateway_validated: bool = False,
    command_gateway_validated: bool = False,
    active_authority_leases: list[AuthorityLease] | None = None,
    kill_switch_engaged: bool = False,
) -> RuntimePolicyDecision:
    profile = RuntimeProfile(request.requested_profile)
    authority_decision = None
    if active_authority_leases is not None:
        resource_refs = [request.mission_ref] if request.mission_ref else []
        authority_constraints = (
            {"mission_ref": request.mission_ref} if request.mission_ref else {}
        )
        if request.requested_authority == RuntimeAuthority.local_model.value:
            authority_request = AuthorityActionRequest(
                action_ref=request.action_ref or invocation_ref,
                domain=AuthorityDomain.provider_model_calls,
                capability=AuthorityCapability.execute,
                safe_summary=(
                    "Evaluate local loopback provider model call authority for "
                    "governed runtime."
                ),
                resource_refs=resource_refs,
                route_ref="POST /api/runtime/local-model/call",
                requested_mode=TrustMode.full_machine_access_session,
                constraints=authority_constraints,
                draft_fallback_available=True,
                kill_switch_engaged=kill_switch_engaged,
            )
        else:
            command_capability = (
                AuthorityCapability.read
                if request.action_ref
                == f"action-ref:runtime-command-{RuntimeCommandIntent.git_status.value}"
                else AuthorityCapability.execute
            )
            authority_request = AuthorityActionRequest(
                action_ref=request.action_ref or invocation_ref,
                domain=AuthorityDomain.workspace,
                capability=command_capability,
                safe_summary="Evaluate workspace command authority for governed runtime.",
                resource_refs=resource_refs,
                route_ref="POST /api/runtime/command/run",
                requested_mode=(
                    TrustMode.read_only
                    if command_capability == AuthorityCapability.read
                    else TrustMode.approved_safe_local_work_session
                ),
                constraints=authority_constraints,
                draft_fallback_available=True,
                kill_switch_engaged=kill_switch_engaged,
            )
        authority_decision = evaluate_authority_request(
            authority_request,
            active_authority_leases,
        )
    authority_allows_execution = (
        authority_decision is None
        or authority_decision.outcome == AuthorityDecisionOutcome.allow.value
    )
    local_model_enabled = (
        request.requested_authority == RuntimeAuthority.local_model.value
        and local_model_gateway_validated
        and authority_allows_execution
        and profile
        in {
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        }
    )
    command_enabled = (
        request.requested_authority == RuntimeAuthority.allowlisted_command.value
        and command_gateway_validated
        and authority_allows_execution
        and profile
        in {
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        }
    )
    approval_requirement = RuntimeApprovalRequirement(
        approval_ref=approval_ref or request.approval_ref,
        approval_validated=False,
        approval_binding_recorded=bool(approval_ref or request.approval_ref),
    )
    if local_model_enabled:
        reason_codes = [
            "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_LOOPBACK",
            "MODEL_OUTPUT_PROPOSAL_ONLY",
        ]
    elif command_enabled:
        reason_codes = [
            "GOVERNED_RUNTIME_PHASE_04_ALLOWLISTED_READONLY_COMMAND",
            "COMMAND_OUTPUT_REDACTED_AND_BOUNDED",
        ]
    elif (
        request.requested_authority == RuntimeAuthority.local_model.value
        and profile
        in {
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        }
        and not local_model_gateway_validated
    ):
        reason_codes = [
            "GOVERNED_RUNTIME_PHASE_03_LOCAL_MODEL_GATEWAY_VALIDATION_REQUIRED",
            "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
        ]
    elif (
        request.requested_authority == RuntimeAuthority.local_model.value
        and profile
        in {
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        }
    ):
        reason_codes = [
            "GOVERNED_RUNTIME_EXECUTION_DISABLED_OR_AUTHORITY_LEASE_REQUIRED",
            "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
        ]
    elif (
        request.requested_authority == RuntimeAuthority.allowlisted_command.value
        and profile
        in {
            RuntimeProfile.local_runtime,
            RuntimeProfile.operator_approved,
        }
    ):
        reason_codes = [
            "GOVERNED_RUNTIME_PHASE_04_COMMAND_GATEWAY_VALIDATION_REQUIRED",
            "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
        ]
    else:
        reason_codes = [
            "GOVERNED_RUNTIME_EXECUTION_DISABLED_OR_AUTHORITY_LEASE_REQUIRED",
            "RUNTIME_ADAPTER_EXECUTION_BLOCKED",
        ]
    if approval_ref or request.approval_ref:
        reason_codes.append("APPROVAL_REF_IDENTIFIER_ONLY")
    if authority_decision is not None:
        reason_codes.append(
            f"AUTHORITY_LEASE_DECISION_{str(authority_decision.outcome).upper()}"
        )
        if authority_decision.outcome != AuthorityDecisionOutcome.allow.value and (
            local_model_gateway_validated or command_gateway_validated
        ):
            reason_codes.append("AUTHORITY_LEASE_REQUIRED_FOR_RUNTIME_EXECUTION")
    return RuntimePolicyDecision(
        policy_decision_ref=runtime_policy_decision_ref(invocation_ref),
        profile=profile
        if local_model_enabled or command_enabled
        else RuntimeProfile.sealed,
        requested_authority=request.requested_authority,
        invocation_status=status,
        allowed_to_execute=local_model_enabled or command_enabled,
        adapter_execution_enabled=local_model_enabled or command_enabled,
        model_call_enabled=local_model_enabled,
        command_execution_enabled=command_enabled,
        approval_requirement=approval_requirement,
        reason_codes=reason_codes,
        authority_decision_ref=(
            authority_decision.decision_ref if authority_decision is not None else None
        ),
        authority_decision_outcome=(
            authority_decision.outcome if authority_decision is not None else None
        ),
        authority_lease_ref=(
            authority_decision.lease_ref if authority_decision is not None else None
        ),
        authority_domain=(
            authority_decision.domain if authority_decision is not None else None
        ),
        authority_capability=(
            authority_decision.capability if authority_decision is not None else None
        ),
        authority_required_mode=(
            authority_decision.required_mode if authority_decision is not None else None
        ),
        authority_reason_refs=(
            list(authority_decision.reason_refs)
            if authority_decision is not None
            else []
        ),
        authority_audit_ref=(
            authority_decision.audit_record_ref
            if authority_decision is not None
            else None
        ),
        authority_policy_receipt_ref=(
            authority_decision.receipt_ref if authority_decision is not None else None
        ),
        authority_rollback_ref=(
            authority_decision.rollback_ref if authority_decision is not None else None
        ),
        authority_safe_disable_ref=(
            authority_decision.safe_disable_ref
            if authority_decision is not None
            else None
        ),
        authority_known_authority=(
            authority_decision.known_authority
            if authority_decision is not None
            else None
        ),
        authority_unsupported_adapter=(
            authority_decision.unsupported_adapter
            if authority_decision is not None
            else None
        ),
        authority_operator_message=(
            authority_decision.operator_message
            if authority_decision is not None
            else None
        ),
        safe_summary=(
            "RuntimeGateway policy allows loopback local model calls as untrusted proposals."
            if local_model_enabled
            else (
                "RuntimeGateway policy allows an exact allowlisted read-only command with redacted output."
                if command_enabled
                else "RuntimeGateway policy recorded a blocked or disabled runtime decision."
            )
        ),
    )


def build_blocked_receipt(
    record: RuntimeInvocationRecord,
    *,
    safe_summary: str = "Runtime execution remains blocked for the requested authority.",
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
                    {
                        "invocation_ref": record.invocation_ref,
                        "kind": "blocked-receipt",
                    },
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
        safe_disable=record.safe_disable,
        safe_summary=safe_summary,
    )


def build_local_model_receipt(
    record: RuntimeInvocationRecord,
    *,
    metadata: RuntimeLocalModelReceiptMetadata,
    execution_performed: bool | None = None,
    model_call_performed: bool | None = None,
    status: RuntimeInvocationStatus = RuntimeInvocationStatus.receipt_recorded,
) -> RuntimeInvocationReceipt:
    if execution_performed is None:
        execution_performed = not metadata.attempt_outcome_unknown
    if model_call_performed is None:
        model_call_performed = not metadata.attempt_outcome_unknown
    receipt_ref = (
        _stable_ref(
            "runtime-receipt-ref",
            {
                "invocation_ref": record.invocation_ref,
                "status": "attempt_outcome_unknown",
            },
        )
        if metadata.attempt_outcome_unknown
        else runtime_receipt_ref(record.invocation_ref, status)
    )
    artifact_kind = (
        "local_model_runtime_attempt_marker"
        if metadata.attempt_outcome_unknown
        else "local_model_runtime_receipt"
    )
    evidence_status = (
        "local-model-attempt-marker"
        if metadata.attempt_outcome_unknown
        else "local-model-receipt"
    )
    return RuntimeInvocationReceipt(
        receipt_ref=receipt_ref,
        invocation_ref=record.invocation_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        invocation_status=status,
        artifact_refs=[
            RuntimeArtifactRef(
                artifact_ref=_stable_ref(
                    "runtime-artifact-ref",
                    {"invocation_ref": record.invocation_ref, "kind": evidence_status},
                ),
                artifact_kind=artifact_kind,
                safe_summary="Local model runtime receipt stores metadata and safe refs only.",
            )
        ],
        evidence_refs=[
            _stable_ref(
                "runtime-evidence-ref",
                {"invocation_ref": record.invocation_ref, "status": evidence_status},
            )
        ],
        blocked_authority_refs=list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS),
        safe_disable=record.safe_disable,
        model_receipt_metadata=metadata,
        execution_performed=execution_performed,
        adapter_execution_performed=execution_performed,
        model_call_performed=model_call_performed,
        command_execution_performed=False,
        connector_write_performed=False,
        browser_automation_performed=False,
        model_output_non_authoritative=True,
        safe_summary=(
            "Local model transport attempt was authorized; its outcome remains unknown."
            if metadata.attempt_outcome_unknown
            else (
                "Local model runtime attempt was blocked before transport; metadata only."
                if status == RuntimeInvocationStatus.execution_blocked
                else "Local model runtime attempt completed; output is an untrusted proposal."
            )
        ),
    )


def build_command_receipt(
    record: RuntimeInvocationRecord,
    *,
    metadata: RuntimeCommandReceiptMetadata,
    execution_performed: bool = True,
    command_execution_performed: bool = True,
    status: RuntimeInvocationStatus = RuntimeInvocationStatus.receipt_recorded,
) -> RuntimeInvocationReceipt:
    return RuntimeInvocationReceipt(
        receipt_ref=runtime_receipt_ref(record.invocation_ref, status),
        invocation_ref=record.invocation_ref,
        policy_decision_ref=record.policy_decision.policy_decision_ref,
        invocation_status=status,
        artifact_refs=[
            RuntimeArtifactRef(
                artifact_ref=_stable_ref(
                    "runtime-artifact-ref",
                    {
                        "invocation_ref": record.invocation_ref,
                        "kind": "command-receipt",
                    },
                ),
                artifact_kind="allowlisted_command_runtime_receipt",
                safe_summary="Command runtime receipt stores safe refs and redacted counts only.",
            )
        ],
        evidence_refs=[
            _stable_ref(
                "runtime-evidence-ref",
                {"invocation_ref": record.invocation_ref, "status": "command-receipt"},
            )
        ],
        blocked_authority_refs=list(GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS),
        safe_disable=record.safe_disable,
        command_receipt_metadata=metadata,
        execution_performed=execution_performed,
        adapter_execution_performed=execution_performed,
        model_call_performed=False,
        command_execution_performed=command_execution_performed,
        connector_write_performed=False,
        browser_automation_performed=False,
        model_output_non_authoritative=True,
        safe_summary=(
            "Allowlisted command runtime attempt was blocked before process start; metadata only."
            if status == RuntimeInvocationStatus.execution_blocked
            else "Allowlisted command runtime completed; output was redacted and bounded."
        ),
    )


def build_default_runtime_capabilities() -> RuntimeCapabilities:
    return RuntimeCapabilities()
