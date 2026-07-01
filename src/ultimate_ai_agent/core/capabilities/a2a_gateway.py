from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.adapters import A2AAgentCardMinimal
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityLatencyClass,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CAPABILITY_SCOPE_PATTERN,
    CapabilityManifest,
    SafetyPolicy,
    _assert_secret_clean,
)


A2A_REVIEW_AUTH_SCOPE = "a2a:reviewed"
A2A_DEFAULT_BLOCKED_AUTHORITY_REFS = (
    "blocked-state-ref:a2a:no-remote-dispatch",
    "blocked-state-ref:a2a:no-peer-auth-runtime",
    "blocked-state-ref:a2a:no-remote-self-approval",
    "blocked-state-ref:a2a:no-connector-write",
    "blocked-state-ref:a2a:no-browser-shell-execution",
    "blocked-state-ref:a2a:no-provider-call",
)
_SAFE_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9_.:-]+")


class A2ATrustPosture(str, Enum):
    unknown_blocked = "unknown_blocked"
    untrusted_metadata = "untrusted_metadata"
    locally_reviewed_metadata = "locally_reviewed_metadata"
    revoked = "revoked"


class A2AAuthPosture(str, Enum):
    unknown_blocked = "unknown_blocked"
    none_declared = "none_declared"
    credential_ref_required = "credential_ref_required"
    peer_auth_blocked = "peer_auth_blocked"
    raw_credential_blocked = "raw_credential_blocked"


class A2AActivationPosture(str, Enum):
    blocked_review_required = "blocked_review_required"
    metadata_only = "metadata_only"
    handoff_preview_only = "handoff_preview_only"


class A2AAgentMetadata(BaseModel):
    agent_ref: str = Field(..., min_length=1)
    card_ref: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    owner_ref: str = Field(..., min_length=1)
    version_ref: str = Field(..., min_length=1)
    schema_version_ref: str = Field(..., min_length=1)
    declared_capability_refs: list[str] = Field(default_factory=list)
    requested_grant_refs: list[str] = Field(default_factory=list)
    endpoint_ref: str = "endpoint-ref:a2a:not-accepted"
    endpoint_declared: bool = False
    provenance_ref: str = Field(..., min_length=1)
    trust_posture: A2ATrustPosture = A2ATrustPosture.unknown_blocked
    auth_posture: A2AAuthPosture = A2AAuthPosture.unknown_blocked
    activation_posture: A2AActivationPosture = A2AActivationPosture.blocked_review_required
    risk_level: RiskLevel = RiskLevel.high
    authority_level: CapabilityAuthorityLevel = CapabilityAuthorityLevel.metadata_only
    privacy_level: CapabilityPrivacyLevel = CapabilityPrivacyLevel.local_private
    estimated_latency_class: CapabilityLatencyClass = CapabilityLatencyClass.unknown
    estimated_cost_class: CapabilityCostClass = CapabilityCostClass.unknown
    credential_ref_required: bool = False
    credential_refs: list[str] = Field(default_factory=list)
    status_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    expected_receipt_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=lambda: list(A2A_DEFAULT_BLOCKED_AUTHORITY_REFS))

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator(
        "agent_ref",
        "card_ref",
        "owner_ref",
        "version_ref",
        "schema_version_ref",
        "endpoint_ref",
        "provenance_ref",
        "status_ref",
        "audit_ref",
        "replay_ref",
        "revocation_ref",
        "safe_disable_ref",
        "expected_receipt_ref",
    )
    @classmethod
    def validate_safe_ref(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator(
        "declared_capability_refs",
        "requested_grant_refs",
        "credential_refs",
        "evidence_refs",
        "blocked_authority_refs",
    )
    @classmethod
    def validate_safe_ref_list(cls, values: list[str]) -> list[str]:
        return [_safe_ref(value) for value in values]

    @model_validator(mode="after")
    def validate_metadata(self) -> "A2AAgentMetadata":
        _assert_secret_clean(self.model_dump(mode="json"), "a2a_agent_metadata")
        if self.auth_posture == A2AAuthPosture.raw_credential_blocked:
            raise ValueError("raw A2A credential material is blocked; use credential refs only.")
        if self.credential_ref_required and not self.credential_refs:
            raise ValueError("credential-ref-required A2A metadata must name safe credential refs.")
        if self.trust_posture == A2ATrustPosture.revoked and self.activation_posture != A2AActivationPosture.blocked_review_required:
            raise ValueError("revoked A2A metadata must remain blocked for review.")
        return self


class A2AHandoffProposalEnvelope(BaseModel):
    proposal_ref: str
    capability_id: str
    source_agent_ref: str
    target_agent_ref: str
    card_ref: str
    task_ref: str
    objective_ref: str
    status: Literal["proposal_only", "blocked_review_required"] = "blocked_review_required"
    declared_input_refs: list[str] = Field(default_factory=list)
    expected_evidence_refs: list[str] = Field(default_factory=list)
    requested_grant_refs: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    delegation_performed: bool = False
    remote_dispatch_allowed: bool = False
    remote_self_approval_allowed: bool = False
    memory_write_allowed: bool = False
    provider_call_allowed: bool = False
    connector_write_allowed: bool = False
    browser_shell_execution_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "A2AHandoffProposalEnvelope":
        _assert_secret_clean(self.model_dump(mode="json"), "a2a_handoff_proposal")
        if self.delegation_performed or self.remote_dispatch_allowed:
            raise ValueError("A2A handoff proposals cannot perform or authorize remote dispatch.")
        if self.remote_self_approval_allowed:
            raise ValueError("A2A handoff proposals cannot allow remote self-approval.")
        if (
            self.memory_write_allowed
            or self.provider_call_allowed
            or self.connector_write_allowed
            or self.browser_shell_execution_allowed
        ):
            raise ValueError("A2A handoff proposals cannot grant runtime authority.")
        return self


class A2AExactDelegationApprovalBinding(BaseModel):
    approval_ref: str
    agent_ref: str
    card_ref: str
    capability_id: str
    task_ref: str
    handoff_ref: str
    requested_grant_refs: list[str] = Field(default_factory=list)
    credential_refs: list[str] = Field(default_factory=list)
    expires_ref: str
    expected_receipt_ref: str
    revocation_ref: str

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "approval_ref",
        "agent_ref",
        "card_ref",
        "capability_id",
        "task_ref",
        "handoff_ref",
        "expires_ref",
        "expected_receipt_ref",
        "revocation_ref",
    )
    @classmethod
    def validate_safe_ref(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator("requested_grant_refs", "credential_refs")
    @classmethod
    def validate_safe_ref_list(cls, values: list[str]) -> list[str]:
        return [_safe_ref(value) for value in values]


class A2AApprovalBindingDecision(BaseModel):
    allowed: bool
    status: Literal["approval_bound", "blocked"]
    reason_codes: list[str]
    safe_message: str
    approval_ref: str | None = None
    capability_id: str
    agent_ref: str

    model_config = ConfigDict(extra="forbid")


class A2ABlockedReceipt(BaseModel):
    receipt_ref: str
    capability_id: str
    agent_ref: str
    card_ref: str
    status: Literal["blocked"] = "blocked"
    reason_codes: list[str]
    safe_summary: str
    approval_ref: str | None = None
    approval_missing_ref: str | None = None
    redacted_task_ref: str
    redacted_status_ref: str
    audit_ref: str
    replay_ref: str
    rollback_ref: str
    delegation_performed: bool = False
    remote_dispatch_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "A2ABlockedReceipt":
        _assert_secret_clean(self.model_dump(mode="json"), "a2a_blocked_receipt")
        if self.delegation_performed or self.remote_dispatch_performed:
            raise ValueError("blocked A2A receipts cannot record delegation or remote dispatch.")
        return self


class A2AReplayAuditRecord(BaseModel):
    replay_ref: str
    capability_id: str
    agent_ref: str
    card_ref: str
    selection_ref: str
    policy_decision_ref: str
    approval_decision_ref: str
    receipt_ref: str
    revocation_ref: str
    reason_codes: list[str]
    reconstructable: bool = True
    redelegation_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_replay(self) -> "A2AReplayAuditRecord":
        _assert_secret_clean(self.model_dump(mode="json"), "a2a_replay_audit_record")
        if self.redelegation_allowed:
            raise ValueError("A2A replay audit records cannot authorize redelegation.")
        return self


def a2a_agent_card_to_metadata(
    card: A2AAgentCardMinimal,
    *,
    provenance_ref: str = "provenance-ref:a2a:unreviewed",
) -> A2AAgentMetadata:
    safe_agent = _safe_token(card.agent_id)
    endpoint_declared = bool(card.endpoint_url)
    return A2AAgentMetadata(
        agent_ref=f"a2a-agent-ref:{safe_agent}",
        card_ref=f"a2a-card-ref:{safe_agent}",
        name=card.name,
        owner_ref=f"owner-ref:a2a:{_safe_token(card.owner)}",
        version_ref=f"version-ref:a2a:{_safe_token(card.version)}",
        schema_version_ref=f"schema-version-ref:{_safe_token(card.schema_version)}",
        declared_capability_refs=[
            f"capability-ref:a2a-declared:{_safe_token(value)}"
            for value in card.declared_capabilities
        ],
        endpoint_ref="endpoint-ref:a2a:declared-redacted" if endpoint_declared else "endpoint-ref:a2a:not-declared",
        endpoint_declared=endpoint_declared,
        provenance_ref=provenance_ref,
        status_ref=f"status-ref:a2a:{safe_agent}:metadata-only",
        audit_ref=f"audit-ref:a2a:{safe_agent}",
        replay_ref=f"replay-ref:a2a:{safe_agent}",
        revocation_ref=f"revocation-ref:a2a:{safe_agent}",
        safe_disable_ref=f"safe-disable-ref:a2a:{safe_agent}",
        expected_receipt_ref=f"receipt-ref:a2a:{safe_agent}:blocked",
        evidence_refs=[f"evidence-ref:a2a:{safe_agent}:agent-card-metadata"],
    )


def a2a_agent_metadata_to_capability_candidate(
    metadata: A2AAgentMetadata,
    *,
    capability_id: str | None = None,
) -> CapabilityManifest:
    return CapabilityManifest(
        id=capability_id or f"capability-ref:a2a:{_safe_token(metadata.agent_ref)}",
        version="0.0.0",
        kind=CapabilityKind.a2a_agent,
        name=metadata.name,
        description="A2A agent-card metadata import. Remote delegation remains blocked.",
        tags=["a2a", "gateway-foundation", "metadata-only"],
        examples=[f"Inspect {metadata.agent_ref} as an A2A delegation candidate after review."],
        anti_examples=[f"Do not delegate to {metadata.agent_ref} from card metadata or model output."],
        input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "additionalProperties": False},
        input_modes=["safe_task_ref", "safe_handoff_ref"],
        output_modes=["blocked_receipt_ref", "proposal_ref"],
        side_effects=SideEffectLevel.none,
        risk_level=metadata.risk_level,
        authority_level=metadata.authority_level,
        approval_required="a2a_exact_delegation_approval_required",
        deterministic=False,
        rollback_supported=False,
        receipt_required=True,
        privacy_level=metadata.privacy_level,
        estimated_latency_class=metadata.estimated_latency_class,
        estimated_cost_class=metadata.estimated_cost_class,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=False,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        auth_scopes=[A2A_REVIEW_AUTH_SCOPE],
        data_classes=["a2a_metadata_safe_refs_only"],
        allowed_coordination_modes=[CoordinationMode.human_gate, CoordinationMode.reviewer],
        concurrency_safe=False,
        single_writer_required=False,
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=False,
            approval_required=True,
            max_risk_level=metadata.risk_level,
            max_side_effect_level=SideEffectLevel.none,
        ),
        metadata={
            "source": "a2a_agent_card_metadata",
            "agent_ref": metadata.agent_ref,
            "card_ref": metadata.card_ref,
            "owner_ref": metadata.owner_ref,
            "version_ref": metadata.version_ref,
            "schema_version_ref": metadata.schema_version_ref,
            "declared_capability_refs": list(metadata.declared_capability_refs),
            "requested_grant_refs": list(metadata.requested_grant_refs),
            "endpoint_ref": metadata.endpoint_ref,
            "endpoint_declared": metadata.endpoint_declared,
            "provenance_ref": metadata.provenance_ref,
            "trust_posture": metadata.trust_posture.value,
            "auth_posture": metadata.auth_posture.value,
            "activation_posture": metadata.activation_posture.value,
            "credential_ref_required": metadata.credential_ref_required,
            "credential_refs": list(metadata.credential_refs),
            "status_ref": metadata.status_ref,
            "audit_ref": metadata.audit_ref,
            "replay_ref": metadata.replay_ref,
            "revocation_ref": metadata.revocation_ref,
            "safe_disable_ref": metadata.safe_disable_ref,
            "expected_receipt_ref": metadata.expected_receipt_ref,
            "evidence_refs": list(metadata.evidence_refs),
            "blocked_authority_refs": list(metadata.blocked_authority_refs),
            "remote_dispatch_allowed": False,
            "peer_auth_runtime_allowed": False,
            "remote_self_approval_allowed": False,
        },
    )


def build_a2a_handoff_proposal(
    metadata: A2AAgentMetadata,
    manifest: CapabilityManifest,
    *,
    proposal_ref: str,
    source_agent_ref: str,
    task_ref: str,
    objective_ref: str,
) -> A2AHandoffProposalEnvelope:
    return A2AHandoffProposalEnvelope(
        proposal_ref=_safe_ref(proposal_ref),
        capability_id=manifest.id,
        source_agent_ref=_safe_ref(source_agent_ref),
        target_agent_ref=metadata.agent_ref,
        card_ref=metadata.card_ref,
        task_ref=_safe_ref(task_ref),
        objective_ref=_safe_ref(objective_ref),
        declared_input_refs=[f"input-ref:a2a:{_safe_token(metadata.agent_ref)}:task"],
        expected_evidence_refs=[metadata.audit_ref, metadata.replay_ref, metadata.expected_receipt_ref],
        requested_grant_refs=list(metadata.requested_grant_refs),
        reason_codes=["A2A_METADATA_ONLY", "A2A_REMOTE_DISPATCH_BLOCKED", "A2A_EXACT_APPROVAL_REQUIRED"],
    )


def evaluate_a2a_exact_approval_binding(
    binding: A2AExactDelegationApprovalBinding,
    metadata: A2AAgentMetadata,
    manifest: CapabilityManifest,
) -> A2AApprovalBindingDecision:
    reason_codes: list[str] = []
    if binding.agent_ref != metadata.agent_ref:
        reason_codes.append("A2A_APPROVAL_AGENT_MISMATCH")
    if binding.card_ref != metadata.card_ref:
        reason_codes.append("A2A_APPROVAL_CARD_MISMATCH")
    if binding.capability_id != manifest.id:
        reason_codes.append("A2A_APPROVAL_CAPABILITY_MISMATCH")
    if binding.expected_receipt_ref != metadata.expected_receipt_ref:
        reason_codes.append("A2A_APPROVAL_RECEIPT_MISMATCH")
    if binding.revocation_ref != metadata.revocation_ref:
        reason_codes.append("A2A_APPROVAL_REVOCATION_MISMATCH")
    missing_grants = sorted(set(metadata.requested_grant_refs) - set(binding.requested_grant_refs))
    if missing_grants:
        reason_codes.append("A2A_APPROVAL_REQUESTED_GRANT_MISSING")
    missing_credentials = sorted(set(metadata.credential_refs) - set(binding.credential_refs))
    if metadata.credential_ref_required and missing_credentials:
        reason_codes.append("A2A_APPROVAL_CREDENTIAL_REF_MISSING")
    if reason_codes:
        return A2AApprovalBindingDecision(
            allowed=False,
            status="blocked",
            reason_codes=reason_codes,
            safe_message="A2A approval binding did not match the exact delegation metadata.",
            approval_ref=binding.approval_ref,
            capability_id=manifest.id,
            agent_ref=metadata.agent_ref,
        )
    return A2AApprovalBindingDecision(
        allowed=True,
        status="approval_bound",
        reason_codes=["A2A_EXACT_APPROVAL_BOUND"],
        safe_message="A2A approval binding matches the metadata contract; remote dispatch remains separately gated.",
        approval_ref=binding.approval_ref,
        capability_id=manifest.id,
        agent_ref=metadata.agent_ref,
    )


def build_a2a_blocked_receipt(
    metadata: A2AAgentMetadata,
    manifest: CapabilityManifest,
    *,
    receipt_ref: str,
    reason_codes: list[str],
    approval_ref: str | None = None,
) -> A2ABlockedReceipt:
    return A2ABlockedReceipt(
        receipt_ref=_safe_ref(receipt_ref),
        capability_id=manifest.id,
        agent_ref=metadata.agent_ref,
        card_ref=metadata.card_ref,
        reason_codes=reason_codes,
        safe_summary="A2A delegation candidate was blocked before remote dispatch.",
        approval_ref=approval_ref,
        approval_missing_ref=None if approval_ref else "approval-missing-ref:a2a:exact-delegation-approval-required",
        redacted_task_ref=f"redacted-task-ref:a2a:{_safe_token(metadata.agent_ref)}",
        redacted_status_ref=f"redacted-status-ref:a2a:{_safe_token(metadata.agent_ref)}",
        audit_ref=metadata.audit_ref,
        replay_ref=metadata.replay_ref,
        rollback_ref=metadata.safe_disable_ref,
    )


def build_a2a_replay_audit_record(
    metadata: A2AAgentMetadata,
    manifest: CapabilityManifest,
    receipt: A2ABlockedReceipt,
    *,
    selection_ref: str,
    policy_decision_ref: str,
    approval_decision_ref: str,
) -> A2AReplayAuditRecord:
    return A2AReplayAuditRecord(
        replay_ref=metadata.replay_ref,
        capability_id=manifest.id,
        agent_ref=metadata.agent_ref,
        card_ref=metadata.card_ref,
        selection_ref=_safe_ref(selection_ref),
        policy_decision_ref=_safe_ref(policy_decision_ref),
        approval_decision_ref=_safe_ref(approval_decision_ref),
        receipt_ref=receipt.receipt_ref,
        revocation_ref=metadata.revocation_ref,
        reason_codes=list(receipt.reason_codes),
    )


def _safe_ref(value: str) -> str:
    if not value or not CAPABILITY_SCOPE_PATTERN.fullmatch(value):
        raise ValueError("A2A refs must be safe refs.")
    return value


def _safe_token(value: str) -> str:
    token = _SAFE_TOKEN_PATTERN.sub("-", value.strip()).strip("-")
    return token or "unknown"
