from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


MCP_REVIEW_AUTH_SCOPE = "mcp:reviewed"
MCP_DEFAULT_BLOCKED_AUTHORITY_REFS = (
    "blocked-state-ref:mcp:no-runtime-invocation",
    "blocked-state-ref:mcp:no-tools-call",
    "blocked-state-ref:mcp:no-server-start",
    "blocked-state-ref:mcp:no-network-transport",
    "blocked-state-ref:mcp:no-oauth-runtime",
    "blocked-state-ref:mcp:no-connector-write",
)
_SAFE_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9_.:-]+")


class McpTransportPosture(str, Enum):
    unknown_blocked = "unknown_blocked"
    metadata_only = "metadata_only"
    local_stdio_blocked = "local_stdio_blocked"
    loopback_blocked = "loopback_blocked"
    remote_network_blocked = "remote_network_blocked"


class McpAuthPosture(str, Enum):
    unknown_blocked = "unknown_blocked"
    none_declared = "none_declared"
    credential_ref_required = "credential_ref_required"
    oauth_blocked = "oauth_blocked"
    raw_credential_blocked = "raw_credential_blocked"


class McpActivationPosture(str, Enum):
    blocked_review_required = "blocked_review_required"
    metadata_only = "metadata_only"
    preview_only = "preview_only"


class McpDiscoveryToolMetadata(BaseModel):
    server_ref: str = Field(..., min_length=1)
    tool_ref: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    output_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object"})
    provenance_ref: str = Field(..., min_length=1)
    transport_posture: McpTransportPosture = McpTransportPosture.unknown_blocked
    auth_posture: McpAuthPosture = McpAuthPosture.unknown_blocked
    activation_posture: McpActivationPosture = McpActivationPosture.blocked_review_required
    declared_side_effects: SideEffectLevel | None = None
    risk_level: RiskLevel = RiskLevel.high
    authority_level: CapabilityAuthorityLevel = CapabilityAuthorityLevel.metadata_only
    privacy_level: CapabilityPrivacyLevel = CapabilityPrivacyLevel.local_private
    estimated_latency_class: CapabilityLatencyClass = CapabilityLatencyClass.unknown
    estimated_cost_class: CapabilityCostClass = CapabilityCostClass.unknown
    credential_ref_required: bool = False
    credential_refs: list[str] = Field(default_factory=list)
    audit_ref: str = Field(..., min_length=1)
    replay_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    expected_receipt_ref: str = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(default_factory=lambda: list(MCP_DEFAULT_BLOCKED_AUTHORITY_REFS))

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator(
        "server_ref",
        "tool_ref",
        "provenance_ref",
        "audit_ref",
        "replay_ref",
        "revocation_ref",
        "safe_disable_ref",
        "expected_receipt_ref",
    )
    @classmethod
    def validate_safe_ref(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator("credential_refs", "blocked_authority_refs")
    @classmethod
    def validate_safe_ref_list(cls, values: list[str]) -> list[str]:
        return [_safe_ref(value) for value in values]

    @model_validator(mode="after")
    def validate_metadata(self) -> "McpDiscoveryToolMetadata":
        _assert_secret_clean(self.model_dump(mode="json"), "mcp_discovery_tool_metadata")
        if self.auth_posture == McpAuthPosture.raw_credential_blocked:
            raise ValueError("raw MCP credential material is blocked; use credential refs only.")
        if self.credential_ref_required and not self.credential_refs:
            raise ValueError("credential-ref-required MCP metadata must name safe credential refs.")
        if self.declared_side_effects is None and self.risk_level not in {RiskLevel.high, RiskLevel.critical}:
            raise ValueError("unknown MCP tool side effects must be high or critical risk.")
        return self


class McpPreviewContract(BaseModel):
    capability_id: str
    server_ref: str
    tool_ref: str
    status: Literal["preview_only", "blocked_review_required"] = "blocked_review_required"
    safe_summary: str
    required_argument_refs: list[str] = Field(default_factory=list)
    expected_evidence_refs: list[str] = Field(default_factory=list)
    expected_receipt_ref: str
    reason_codes: list[str] = Field(default_factory=list)
    execution_performed: bool = False
    side_effects_performed: bool = False
    broker_invocation_allowed: bool = False
    model_direct_call_allowed: bool = False
    provider_direct_call_allowed: bool = False
    react_direct_call_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_preview(self) -> "McpPreviewContract":
        _assert_secret_clean(self.model_dump(mode="json"), "mcp_preview_contract")
        if self.execution_performed or self.side_effects_performed:
            raise ValueError("MCP preview contracts cannot perform execution or side effects.")
        if self.broker_invocation_allowed or self.model_direct_call_allowed or self.provider_direct_call_allowed:
            raise ValueError("MCP preview contracts cannot authorize invocation.")
        if self.react_direct_call_allowed:
            raise ValueError("React cannot directly call MCP.")
        return self


class McpExactApprovalBinding(BaseModel):
    approval_ref: str
    server_ref: str
    tool_ref: str
    capability_id: str
    argument_ref: str
    scope_ref: str
    credential_refs: list[str] = Field(default_factory=list)
    budget_ref: str
    expires_ref: str
    expected_receipt_ref: str
    revocation_ref: str

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "approval_ref",
        "server_ref",
        "tool_ref",
        "capability_id",
        "argument_ref",
        "scope_ref",
        "budget_ref",
        "expires_ref",
        "expected_receipt_ref",
        "revocation_ref",
    )
    @classmethod
    def validate_safe_ref(cls, value: str) -> str:
        return _safe_ref(value)

    @field_validator("credential_refs")
    @classmethod
    def validate_safe_ref_list(cls, values: list[str]) -> list[str]:
        return [_safe_ref(value) for value in values]


class McpApprovalBindingDecision(BaseModel):
    allowed: bool
    status: Literal["approval_bound", "blocked"]
    reason_codes: list[str]
    safe_message: str
    approval_ref: str | None = None
    capability_id: str
    tool_ref: str

    model_config = ConfigDict(extra="forbid")


class McpBlockedReceipt(BaseModel):
    receipt_ref: str
    capability_id: str
    server_ref: str
    tool_ref: str
    status: Literal["blocked"] = "blocked"
    reason_codes: list[str]
    safe_summary: str
    approval_ref: str | None = None
    approval_missing_ref: str | None = None
    redacted_input_ref: str
    redacted_output_ref: str
    audit_ref: str
    replay_ref: str
    rollback_ref: str
    execution_performed: bool = False
    side_effects_performed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self) -> "McpBlockedReceipt":
        _assert_secret_clean(self.model_dump(mode="json"), "mcp_blocked_receipt")
        if self.execution_performed or self.side_effects_performed:
            raise ValueError("blocked MCP receipts cannot record execution or side effects.")
        return self


class McpReplayAuditRecord(BaseModel):
    replay_ref: str
    capability_id: str
    server_ref: str
    tool_ref: str
    selection_ref: str
    policy_decision_ref: str
    approval_decision_ref: str
    receipt_ref: str
    revocation_ref: str
    reason_codes: list[str]
    reconstructable: bool = True
    reexecution_allowed: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_replay(self) -> "McpReplayAuditRecord":
        _assert_secret_clean(self.model_dump(mode="json"), "mcp_replay_audit_record")
        if self.reexecution_allowed:
            raise ValueError("MCP replay audit records cannot authorize re-execution.")
        return self


def mcp_tool_metadata_to_capability_candidate(
    metadata: McpDiscoveryToolMetadata,
    *,
    capability_id: str | None = None,
) -> CapabilityManifest:
    side_effects = metadata.declared_side_effects or SideEffectLevel.none
    authority_level = _authority_for_side_effect(side_effects, metadata.authority_level)
    single_writer_required = side_effects in {SideEffectLevel.write, SideEffectLevel.external, SideEffectLevel.destructive}
    return CapabilityManifest(
        id=capability_id or f"capability-ref:mcp:{_safe_token(metadata.tool_ref)}",
        version="0.0.0",
        kind=CapabilityKind.mcp_tool,
        name=metadata.name,
        description=metadata.description,
        tags=["mcp", "gateway-foundation", "metadata-only"],
        examples=[f"Inspect {metadata.tool_ref} as an MCP capability candidate after review."],
        anti_examples=[f"Do not call {metadata.tool_ref} from MCP metadata or model output."],
        input_schema=metadata.input_schema,
        output_schema=metadata.output_schema,
        input_modes=["safe_argument_ref"],
        output_modes=["blocked_receipt_ref", "preview_ref"],
        side_effects=side_effects,
        risk_level=metadata.risk_level,
        authority_level=authority_level,
        approval_required="mcp_exact_approval_required",
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
        auth_scopes=[MCP_REVIEW_AUTH_SCOPE],
        data_classes=["mcp_metadata_safe_refs_only"],
        allowed_coordination_modes=[CoordinationMode.human_gate, CoordinationMode.reviewer],
        concurrency_safe=False,
        single_writer_required=single_writer_required,
        safety=SafetyPolicy(
            allow_parallel=False,
            require_single_writer=single_writer_required,
            approval_required=True,
            max_risk_level=metadata.risk_level,
            max_side_effect_level=side_effects,
        ),
        metadata={
            "source": "mcp_discovery_metadata",
            "server_ref": metadata.server_ref,
            "tool_ref": metadata.tool_ref,
            "provenance_ref": metadata.provenance_ref,
            "transport_posture": metadata.transport_posture.value,
            "auth_posture": metadata.auth_posture.value,
            "activation_posture": metadata.activation_posture.value,
            "credential_ref_required": metadata.credential_ref_required,
            "credential_refs": list(metadata.credential_refs),
            "audit_ref": metadata.audit_ref,
            "replay_ref": metadata.replay_ref,
            "revocation_ref": metadata.revocation_ref,
            "safe_disable_ref": metadata.safe_disable_ref,
            "expected_receipt_ref": metadata.expected_receipt_ref,
            "blocked_authority_refs": list(metadata.blocked_authority_refs),
            "broker_invocation_allowed": False,
            "mcp_tools_call_allowed": False,
            "server_start_allowed": False,
            "network_transport_allowed": False,
            "oauth_runtime_allowed": False,
        },
    )


def build_mcp_preview_contract(
    metadata: McpDiscoveryToolMetadata,
    manifest: CapabilityManifest,
) -> McpPreviewContract:
    required = metadata.input_schema.get("required", [])
    argument_refs = [f"argument-ref:mcp:{_safe_token(metadata.tool_ref)}:{_safe_token(str(item))}" for item in required]
    return McpPreviewContract(
        capability_id=manifest.id,
        server_ref=metadata.server_ref,
        tool_ref=metadata.tool_ref,
        safe_summary="MCP candidate preview is metadata-only and blocked until exact review and approval.",
        required_argument_refs=argument_refs,
        expected_evidence_refs=[
            metadata.audit_ref,
            metadata.replay_ref,
            metadata.expected_receipt_ref,
        ],
        expected_receipt_ref=metadata.expected_receipt_ref,
        reason_codes=["MCP_METADATA_ONLY", "MCP_RUNTIME_BLOCKED", "MCP_EXACT_APPROVAL_REQUIRED"],
    )


def evaluate_mcp_exact_approval_binding(
    binding: McpExactApprovalBinding,
    metadata: McpDiscoveryToolMetadata,
    manifest: CapabilityManifest,
) -> McpApprovalBindingDecision:
    reason_codes: list[str] = []
    if binding.server_ref != metadata.server_ref:
        reason_codes.append("MCP_APPROVAL_SERVER_MISMATCH")
    if binding.tool_ref != metadata.tool_ref:
        reason_codes.append("MCP_APPROVAL_TOOL_MISMATCH")
    if binding.capability_id != manifest.id:
        reason_codes.append("MCP_APPROVAL_CAPABILITY_MISMATCH")
    if binding.expected_receipt_ref != metadata.expected_receipt_ref:
        reason_codes.append("MCP_APPROVAL_RECEIPT_MISMATCH")
    if binding.revocation_ref != metadata.revocation_ref:
        reason_codes.append("MCP_APPROVAL_REVOCATION_MISMATCH")
    missing_credentials = sorted(set(metadata.credential_refs) - set(binding.credential_refs))
    if metadata.credential_ref_required and missing_credentials:
        reason_codes.append("MCP_APPROVAL_CREDENTIAL_REF_MISSING")
    if reason_codes:
        return McpApprovalBindingDecision(
            allowed=False,
            status="blocked",
            reason_codes=reason_codes,
            safe_message="MCP approval binding did not match the exact metadata contract.",
            approval_ref=binding.approval_ref,
            capability_id=manifest.id,
            tool_ref=metadata.tool_ref,
        )
    return McpApprovalBindingDecision(
        allowed=True,
        status="approval_bound",
        reason_codes=["MCP_EXACT_APPROVAL_BOUND"],
        safe_message="MCP approval binding matches the exact metadata contract; runtime remains separately gated.",
        approval_ref=binding.approval_ref,
        capability_id=manifest.id,
        tool_ref=metadata.tool_ref,
    )


def build_mcp_blocked_receipt(
    metadata: McpDiscoveryToolMetadata,
    manifest: CapabilityManifest,
    *,
    receipt_ref: str,
    reason_codes: list[str],
    approval_ref: str | None = None,
) -> McpBlockedReceipt:
    safe_receipt_ref = _safe_ref(receipt_ref)
    return McpBlockedReceipt(
        receipt_ref=safe_receipt_ref,
        capability_id=manifest.id,
        server_ref=metadata.server_ref,
        tool_ref=metadata.tool_ref,
        reason_codes=reason_codes,
        safe_summary="MCP capability candidate was blocked before runtime invocation.",
        approval_ref=approval_ref,
        approval_missing_ref=None if approval_ref else "approval-missing-ref:mcp:exact-approval-required",
        redacted_input_ref=f"redacted-input-ref:mcp:{_safe_token(metadata.tool_ref)}",
        redacted_output_ref=f"redacted-output-ref:mcp:{_safe_token(metadata.tool_ref)}",
        audit_ref=metadata.audit_ref,
        replay_ref=metadata.replay_ref,
        rollback_ref=metadata.safe_disable_ref,
    )


def build_mcp_replay_audit_record(
    metadata: McpDiscoveryToolMetadata,
    manifest: CapabilityManifest,
    receipt: McpBlockedReceipt,
    *,
    selection_ref: str,
    policy_decision_ref: str,
    approval_decision_ref: str,
) -> McpReplayAuditRecord:
    return McpReplayAuditRecord(
        replay_ref=metadata.replay_ref,
        capability_id=manifest.id,
        server_ref=metadata.server_ref,
        tool_ref=metadata.tool_ref,
        selection_ref=_safe_ref(selection_ref),
        policy_decision_ref=_safe_ref(policy_decision_ref),
        approval_decision_ref=_safe_ref(approval_decision_ref),
        receipt_ref=receipt.receipt_ref,
        revocation_ref=metadata.revocation_ref,
        reason_codes=list(receipt.reason_codes),
    )


def _authority_for_side_effect(
    side_effects: SideEffectLevel,
    declared: CapabilityAuthorityLevel,
) -> CapabilityAuthorityLevel:
    if side_effects == SideEffectLevel.write:
        return CapabilityAuthorityLevel.mutating
    if side_effects == SideEffectLevel.external:
        return CapabilityAuthorityLevel.external
    if side_effects == SideEffectLevel.destructive:
        return CapabilityAuthorityLevel.destructive
    return declared


def _safe_ref(value: str) -> str:
    if not value or not CAPABILITY_SCOPE_PATTERN.fullmatch(value):
        raise ValueError("MCP refs must be safe refs.")
    return value


def _safe_token(value: str) -> str:
    token = _SAFE_TOKEN_PATTERN.sub("-", value.strip()).strip("-")
    return token or "unknown"
