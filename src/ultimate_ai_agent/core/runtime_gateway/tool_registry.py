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
from ultimate_ai_agent.core.runtime_gateway.capability_discovery import (
    RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
)
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)
from ultimate_ai_agent.core.tools.v2 import (
    ToolApprovalRequirement,
    ToolCatalogEntry,
    ToolRiskClass,
    ToolSideEffectKind,
    ToolTargetKind,
    build_default_tool_catalog,
)


RUNTIME_TOOL_REGISTRY_CONTRACT_REF = (
    "contract-ref:runtime-tool-registry-availability:v1"
)
RUNTIME_TOOL_REGISTRY_ROUTE_REF = "GET /api/runtime/tool-registry"
RUNTIME_TOOL_REGISTRY_CLI_REF = "uaa runtime inspect-tool-registry"
RUNTIME_TOOL_REGISTRY_SNAPSHOT_REF = (
    "tool-registry-snapshot-ref:runtime:static-availability"
)
RUNTIME_TOOL_REGISTRY_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-10:tool-registry"
)
RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-tool-registry-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}


class RuntimeToolAvailabilityStatus(str, Enum):
    available_metadata_only = "available_metadata_only"
    configured_disabled = "configured_disabled"
    approval_required_future_lane = "approval_required_future_lane"
    blocked = "blocked"
    unsupported = "unsupported"


class RuntimeToolConfiguredStatus(str, Enum):
    configured_metadata_only = "configured_metadata_only"
    configured_disabled = "configured_disabled"
    unconfigured = "unconfigured"
    blocked_by_policy = "blocked_by_policy"
    unsupported = "unsupported"


class RuntimeToolAuthorityClass(str, Enum):
    validation_only = "validation_only"
    preview_only = "preview_only"
    approval_required_future_lane = "approval_required_future_lane"
    blocked_high_authority = "blocked_high_authority"
    unsupported = "unsupported"


class RuntimeToolOrigin(str, Enum):
    uaa_native = "uaa_native"
    hermes_reference = "hermes_reference"
    codex_reference = "codex_reference"
    claude_reference = "claude_reference"
    mcp_reference = "mcp_reference"
    future_runtime_reference = "future_runtime_reference"


class RuntimeToolRegistryEntry(BaseModel):
    tool_ref: str
    tool_id: str
    display_label: str
    origin: RuntimeToolOrigin
    runtime_ref: str
    toolset_ref: str
    availability_status: RuntimeToolAvailabilityStatus
    configured_status: RuntimeToolConfiguredStatus
    authority_class: RuntimeToolAuthorityClass
    target_kind: str
    side_effect_class: str
    risk_class: str
    approval_requirement: str
    safe_summary: str
    uaa_native_catalog_entry: bool = False
    runtime_supported_by_reference: bool = False
    uaa_available_for_preview: bool = False
    uaa_allows_invocation: bool = False
    execution_enabled: bool = False
    remote_discovery_performed: bool = False
    live_web_fetch_performed: bool = False
    provider_model_call_performed: bool = False
    plugin_import_enabled: bool = False
    connector_write_activation_enabled: bool = False
    raw_tool_payload_persisted: bool = False
    approval_scope_ref: str
    safe_disable_ref: str
    receipt_plan_ref: str
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_entry(self) -> "RuntimeToolRegistryEntry":
        for value, field_name in [
            (self.tool_ref, "tool_ref"),
            (self.runtime_ref, "runtime_ref"),
            (self.toolset_ref, "toolset_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "proof_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.tool_id, "tool_id"),
            (self.display_label, "display_label"),
            (self.target_kind, "target_kind"),
            (self.side_effect_class, "side_effect_class"),
            (self.risk_class, "risk_class"),
            (self.approval_requirement, "approval_requirement"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        denied_flags = {
            "uaa_allows_invocation": self.uaa_allows_invocation,
            "execution_enabled": self.execution_enabled,
            "remote_discovery_performed": self.remote_discovery_performed,
            "live_web_fetch_performed": self.live_web_fetch_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "plugin_import_enabled": self.plugin_import_enabled,
            "connector_write_activation_enabled": self.connector_write_activation_enabled,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_TOOL_REGISTRY_INVOCATION_DENIED: " + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_TOOL_REGISTRY_BLOCKERS_REQUIRED")
        if not self.next_safe_action_refs:
            raise ValueError("RUNTIME_TOOL_REGISTRY_NEXT_ACTION_REQUIRED")
        if self.uaa_available_for_preview and self.side_effect_class != "none":
            raise ValueError("RUNTIME_TOOL_REGISTRY_PREVIEW_REQUIRES_NO_EFFECT")
        if (
            self.authority_class
            == RuntimeToolAuthorityClass.blocked_high_authority.value
            and "blocked-authority:runtime-tool-registry-high-authority"
            not in self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_TOOL_REGISTRY_HIGH_AUTHORITY_BLOCKER_REQUIRED")
        return self


class RuntimeToolRegistryAvailabilityReadModel(BaseModel):
    schema_version: str = "runtime_tool_registry_availability.v1"
    contract_ref: str = RUNTIME_TOOL_REGISTRY_CONTRACT_REF
    status: str = "read_only_tool_registry_availability"
    snapshot_ref: str = RUNTIME_TOOL_REGISTRY_SNAPSHOT_REF
    snapshot_hash_ref: str
    route_ref: str = RUNTIME_TOOL_REGISTRY_ROUTE_REF
    cli_ref: str = RUNTIME_TOOL_REGISTRY_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    capability_discovery_route_ref: str = RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF
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
    safe_summary: str = (
        "Runtime tool registry availability is static metadata; tool invocation, "
        "remote discovery, imports, connector activation, and runtime writes remain blocked."
    )
    entries: list[RuntimeToolRegistryEntry]
    tool_count: int = 0
    uaa_native_count: int = 0
    delegated_reference_count: int = 0
    available_metadata_only_count: int = 0
    configured_disabled_count: int = 0
    approval_required_future_count: int = 0
    blocked_count: int = 0
    unsupported_count: int = 0
    invocation_enabled_count: int = 0
    preview_available_count: int = 0
    tool_invocation_enabled: bool = False
    remote_discovery_enabled: bool = False
    live_web_fetch_enabled: bool = False
    provider_model_call_enabled: bool = False
    plugin_import_enabled: bool = False
    connector_write_activation_enabled: bool = False
    raw_tool_payload_persisted: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS) + ["tool_payload_omitted"]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeToolRegistryAvailabilityReadModel":
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
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.capability_discovery_route_ref, "capability_discovery_route_ref"),
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
            validate_safe_execution_text(str(value), field_name)
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redactions_applied")
        if not self.entries:
            raise ValueError("RUNTIME_TOOL_REGISTRY_ENTRIES_REQUIRED")
        if self.tool_count != len(self.entries):
            raise ValueError("RUNTIME_TOOL_REGISTRY_COUNT_MISMATCH")
        if self.uaa_native_count != sum(
            1
            for entry in self.entries
            if entry.origin == RuntimeToolOrigin.uaa_native.value
        ):
            raise ValueError("RUNTIME_TOOL_REGISTRY_UAA_NATIVE_COUNT_MISMATCH")
        if self.delegated_reference_count != sum(
            1
            for entry in self.entries
            if entry.origin != RuntimeToolOrigin.uaa_native.value
        ):
            raise ValueError("RUNTIME_TOOL_REGISTRY_DELEGATED_COUNT_MISMATCH")
        status_counts = {
            RuntimeToolAvailabilityStatus.available_metadata_only.value: self.available_metadata_only_count,
            RuntimeToolAvailabilityStatus.configured_disabled.value: self.configured_disabled_count,
            RuntimeToolAvailabilityStatus.approval_required_future_lane.value: self.approval_required_future_count,
            RuntimeToolAvailabilityStatus.blocked.value: self.blocked_count,
            RuntimeToolAvailabilityStatus.unsupported.value: self.unsupported_count,
        }
        for status, expected_count in status_counts.items():
            actual_count = sum(
                1 for entry in self.entries if entry.availability_status == status
            )
            if expected_count != actual_count:
                raise ValueError("RUNTIME_TOOL_REGISTRY_STATUS_COUNT_MISMATCH")
        if self.invocation_enabled_count != sum(
            1 for entry in self.entries if entry.uaa_allows_invocation
        ):
            raise ValueError("RUNTIME_TOOL_REGISTRY_INVOCATION_COUNT_MISMATCH")
        if self.preview_available_count != sum(
            1 for entry in self.entries if entry.uaa_available_for_preview
        ):
            raise ValueError("RUNTIME_TOOL_REGISTRY_PREVIEW_COUNT_MISMATCH")
        if self.invocation_enabled_count != 0:
            raise ValueError("RUNTIME_TOOL_REGISTRY_INVOCATION_COUNT_DENIED")
        if self.authority_state_mapping_ref != RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_REF:
            raise ValueError("RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_TOOL_REGISTRY_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "tool_invocation_enabled": self.tool_invocation_enabled,
            "remote_discovery_enabled": self.remote_discovery_enabled,
            "live_web_fetch_enabled": self.live_web_fetch_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "plugin_import_enabled": self.plugin_import_enabled,
            "connector_write_activation_enabled": self.connector_write_activation_enabled,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_TOOL_REGISTRY_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if RUNTIME_TOOL_REGISTRY_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_TOOL_REGISTRY_PHASE_PROOF_REQUIRED")
        return self


def _safe_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _entry_from_catalog(tool: ToolCatalogEntry) -> RuntimeToolRegistryEntry:
    slug = _safe_slug(tool.tool_id)
    return RuntimeToolRegistryEntry(
        tool_ref=f"tool-registry-entry-ref:uaa-native:{slug}",
        tool_id=tool.tool_id,
        display_label=tool.display_name,
        origin=RuntimeToolOrigin.uaa_native,
        runtime_ref="runtime-identity-ref:uaa-native:python-core",
        toolset_ref="toolset-ref:runtime:core-readonly-metadata",
        availability_status=RuntimeToolAvailabilityStatus.available_metadata_only,
        configured_status=RuntimeToolConfiguredStatus.configured_metadata_only,
        authority_class=RuntimeToolAuthorityClass.preview_only,
        target_kind=tool.target_kind.value,
        side_effect_class="none",
        risk_class=tool.risk_class.value,
        approval_requirement=tool.approval_requirement.value,
        safe_summary=tool.safe_description
        or "UAA-native validation-only metadata preview.",
        uaa_native_catalog_entry=True,
        runtime_supported_by_reference=False,
        uaa_available_for_preview=True,
        approval_scope_ref=f"approval-scope-ref:tool-registry:{slug}:not-required",
        safe_disable_ref=f"safe-disable-ref:tool-registry:{slug}:registry-only",
        receipt_plan_ref=f"receipt-plan-ref:tool-registry:{slug}:preview-only",
        proof_refs=[RUNTIME_TOOL_REGISTRY_PROOF_REF],
        blocked_authority_refs=[
            "blocked-authority:runtime-tool-registry-invocation",
            "blocked-authority:runtime-tool-registry-execution",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-tool-registry:keep-preview-metadata-only"
        ],
    )


def _reference_entry(
    *,
    tool_id: str,
    display_label: str,
    origin: RuntimeToolOrigin,
    toolset_ref: str,
    availability_status: RuntimeToolAvailabilityStatus,
    configured_status: RuntimeToolConfiguredStatus,
    authority_class: RuntimeToolAuthorityClass,
    target_kind: ToolTargetKind,
    side_effect_class: ToolSideEffectKind,
    risk_class: ToolRiskClass,
    approval_requirement: ToolApprovalRequirement,
    safe_summary: str,
    blocked_authority_refs: list[str],
    next_safe_action_refs: list[str],
    runtime_supported_by_reference: bool = True,
) -> RuntimeToolRegistryEntry:
    slug = _safe_slug(tool_id)
    return RuntimeToolRegistryEntry(
        tool_ref=f"tool-registry-entry-ref:{origin.value}:{slug}",
        tool_id=tool_id,
        display_label=display_label,
        origin=origin,
        runtime_ref=f"runtime-identity-ref:{origin.value}:optional-reference",
        toolset_ref=toolset_ref,
        availability_status=availability_status,
        configured_status=configured_status,
        authority_class=authority_class,
        target_kind=target_kind.value,
        side_effect_class=side_effect_class.value,
        risk_class=risk_class.value,
        approval_requirement=approval_requirement.value,
        safe_summary=safe_summary,
        runtime_supported_by_reference=runtime_supported_by_reference,
        approval_scope_ref=f"approval-scope-ref:tool-registry:{slug}:future",
        safe_disable_ref=f"safe-disable-ref:tool-registry:{slug}:disabled",
        receipt_plan_ref=f"receipt-plan-ref:tool-registry:{slug}:not-executed",
        proof_refs=[RUNTIME_TOOL_REGISTRY_PROOF_REF],
        blocked_authority_refs=blocked_authority_refs,
        next_safe_action_refs=next_safe_action_refs,
    )


def _build_entries() -> list[RuntimeToolRegistryEntry]:
    native_entries = [
        _entry_from_catalog(tool)
        for tool in sorted(
            build_default_tool_catalog().values(), key=lambda item: item.tool_id
        )
    ]
    reference_entries = [
        _reference_entry(
            tool_id="hermes.coding_workspace_context",
            display_label="Hermes coding workspace context",
            origin=RuntimeToolOrigin.hermes_reference,
            toolset_ref="toolset-ref:runtime:coding-workspace",
            availability_status=RuntimeToolAvailabilityStatus.approval_required_future_lane,
            configured_status=RuntimeToolConfiguredStatus.configured_disabled,
            authority_class=RuntimeToolAuthorityClass.approval_required_future_lane,
            target_kind=ToolTargetKind.context_pack_ref,
            side_effect_class=ToolSideEffectKind.context_injection,
            risk_class=ToolRiskClass.high,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Hermes coding context tools need exact context refs, approval, "
                "retrieval logs, and proof before use."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-invocation",
                "blocked-authority:runtime-context-injection",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:define-context-tool-grant"
            ],
        ),
        _reference_entry(
            tool_id="hermes.command_execution",
            display_label="Hermes command execution",
            origin=RuntimeToolOrigin.hermes_reference,
            toolset_ref="toolset-ref:runtime:command-execution",
            availability_status=RuntimeToolAvailabilityStatus.blocked,
            configured_status=RuntimeToolConfiguredStatus.blocked_by_policy,
            authority_class=RuntimeToolAuthorityClass.blocked_high_authority,
            target_kind=ToolTargetKind.local_runtime_ref,
            side_effect_class=ToolSideEffectKind.shell_execution,
            risk_class=ToolRiskClass.critical,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Command execution tools require an explicit AuthorityLease "
                "domain/capability grant plus argv-only RuntimeGateway approval, "
                "redaction, and receipts."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-high-authority",
                "blocked-authority:runtime-command-execution-without-gateway-allowlist",
                "blocked-authority:runtime-unrestricted-command-execution",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:bind-command-allowlist"
            ],
        ),
        _reference_entry(
            tool_id="codex.patch_proposal_review",
            display_label="Codex patch proposal review",
            origin=RuntimeToolOrigin.codex_reference,
            toolset_ref="toolset-ref:runtime:coding-workspace",
            availability_status=RuntimeToolAvailabilityStatus.approval_required_future_lane,
            configured_status=RuntimeToolConfiguredStatus.configured_disabled,
            authority_class=RuntimeToolAuthorityClass.approval_required_future_lane,
            target_kind=ToolTargetKind.file_ref,
            side_effect_class=ToolSideEffectKind.file_write,
            risk_class=ToolRiskClass.high,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Codex patch tools are proposal metadata only until files/write "
                "or workspace/write AuthorityLease scope, exact patch apply, "
                "checkpoint, and rollback receipts exist."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-invocation",
                "blocked-authority:runtime-file-mutation-without-patch-lane",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:bind-patch-proposal-receipts"
            ],
        ),
        _reference_entry(
            tool_id="claude.review_summary",
            display_label="Claude review summary",
            origin=RuntimeToolOrigin.claude_reference,
            toolset_ref="toolset-ref:runtime:core-readonly-metadata",
            availability_status=RuntimeToolAvailabilityStatus.configured_disabled,
            configured_status=RuntimeToolConfiguredStatus.unconfigured,
            authority_class=RuntimeToolAuthorityClass.approval_required_future_lane,
            target_kind=ToolTargetKind.context_pack_ref,
            side_effect_class=ToolSideEffectKind.model_call,
            risk_class=ToolRiskClass.high,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Claude review tooling is a future provider/runtime reference; "
                "UAA does not call providers or persist raw responses here."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-invocation",
                "blocked-authority:runtime-remote-provider-model-call",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:define-provider-review-envelope"
            ],
        ),
        _reference_entry(
            tool_id="mcp.catalog_metadata",
            display_label="MCP catalog metadata",
            origin=RuntimeToolOrigin.mcp_reference,
            toolset_ref="toolset-ref:runtime:plugin-runtime-import",
            availability_status=RuntimeToolAvailabilityStatus.configured_disabled,
            configured_status=RuntimeToolConfiguredStatus.configured_disabled,
            authority_class=RuntimeToolAuthorityClass.approval_required_future_lane,
            target_kind=ToolTargetKind.plugin_ref,
            side_effect_class=ToolSideEffectKind.plugin_enablement,
            risk_class=ToolRiskClass.high,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "MCP tool metadata can be inspected only after review; runtime "
                "plugin import and execution remain blocked."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-invocation",
                "blocked-authority:runtime-plugin-import",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:add-adaptation-review"
            ],
        ),
        _reference_entry(
            tool_id="future.browser_observe",
            display_label="Browser observe tool",
            origin=RuntimeToolOrigin.future_runtime_reference,
            toolset_ref="toolset-ref:runtime:web-browser",
            availability_status=RuntimeToolAvailabilityStatus.blocked,
            configured_status=RuntimeToolConfiguredStatus.blocked_by_policy,
            authority_class=RuntimeToolAuthorityClass.blocked_high_authority,
            target_kind=ToolTargetKind.browser_ref,
            side_effect_class=ToolSideEffectKind.browser_action,
            risk_class=ToolRiskClass.critical,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Browser observe/action tools remain blocked until WebAccessGateway "
                "transport is mapped to browser AuthorityLease capabilities with "
                "policy, redaction, and receipts."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-high-authority",
                "blocked-authority:runtime-browser-automation",
                "blocked-authority:runtime-web-fetch-without-gateway",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:define-browser-observe-gate"
            ],
        ),
        _reference_entry(
            tool_id="future.connector_write",
            display_label="Connector write tool",
            origin=RuntimeToolOrigin.future_runtime_reference,
            toolset_ref="toolset-ref:runtime:connector-write",
            availability_status=RuntimeToolAvailabilityStatus.blocked,
            configured_status=RuntimeToolConfiguredStatus.blocked_by_policy,
            authority_class=RuntimeToolAuthorityClass.blocked_high_authority,
            target_kind=ToolTargetKind.remote_node_ref,
            side_effect_class=ToolSideEffectKind.external_send,
            risk_class=ToolRiskClass.critical,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Connector write tools remain blocked until the target connector "
                "domain has AuthorityLease-gated draft, send/write, approval, "
                "receipt, and rollback posture."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-tool-registry-high-authority",
                "blocked-authority:runtime-connector-write",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:define-connector-write-lane"
            ],
        ),
        _reference_entry(
            tool_id="future.production_operation",
            display_label="Production operation tool",
            origin=RuntimeToolOrigin.future_runtime_reference,
            toolset_ref="toolset-ref:runtime:production-ops",
            availability_status=RuntimeToolAvailabilityStatus.unsupported,
            configured_status=RuntimeToolConfiguredStatus.unsupported,
            authority_class=RuntimeToolAuthorityClass.unsupported,
            target_kind=ToolTargetKind.remote_node_ref,
            side_effect_class=ToolSideEffectKind.remote_execution,
            risk_class=ToolRiskClass.forbidden,
            approval_requirement=ToolApprovalRequirement.future_runtime_approval_required,
            safe_summary=(
                "Production operation tools are unsupported by this pilot and "
                "cannot be enabled by runtime capability metadata."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-production-authority",
                "blocked-authority:runtime-remote-execution",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-tool-registry:keep-production-blocked"
            ],
            runtime_supported_by_reference=False,
        ),
    ]
    return [*native_entries, *reference_entries]


def _snapshot_hash_ref(
    entries: list[RuntimeToolRegistryEntry],
    authority_entry: AuthorityDecisionCatalogEntry,
) -> str:
    payload = {
        "contract_ref": RUNTIME_TOOL_REGISTRY_CONTRACT_REF,
        "snapshot_ref": RUNTIME_TOOL_REGISTRY_SNAPSHOT_REF,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-tool-registry:{digest[:16]}"


def build_runtime_tool_registry_availability_read_model() -> (
    RuntimeToolRegistryAvailabilityReadModel
):
    authority_entry = _authority_entry(authority_decision_catalog=None)
    return build_runtime_tool_registry_availability_read_model_from_authority_catalog(
        authority_decision_catalog=[authority_entry]
    )


def build_runtime_tool_registry_availability_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeToolRegistryAvailabilityReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    entries = _build_entries()
    return RuntimeToolRegistryAvailabilityReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(entries, authority_entry),
        entries=entries,
        authority_state_route_ref=RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_TOOL_REGISTRY_AUTHORITY_STATE_CLI_REF,
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
        tool_count=len(entries),
        uaa_native_count=sum(
            1 for entry in entries if entry.origin == RuntimeToolOrigin.uaa_native.value
        ),
        delegated_reference_count=sum(
            1 for entry in entries if entry.origin != RuntimeToolOrigin.uaa_native.value
        ),
        available_metadata_only_count=sum(
            1
            for entry in entries
            if entry.availability_status
            == RuntimeToolAvailabilityStatus.available_metadata_only.value
        ),
        configured_disabled_count=sum(
            1
            for entry in entries
            if entry.availability_status
            == RuntimeToolAvailabilityStatus.configured_disabled.value
        ),
        approval_required_future_count=sum(
            1
            for entry in entries
            if entry.availability_status
            == RuntimeToolAvailabilityStatus.approval_required_future_lane.value
        ),
        blocked_count=sum(
            1
            for entry in entries
            if entry.availability_status == RuntimeToolAvailabilityStatus.blocked.value
        ),
        unsupported_count=sum(
            1
            for entry in entries
            if entry.availability_status
            == RuntimeToolAvailabilityStatus.unsupported.value
        ),
        preview_available_count=sum(
            1 for entry in entries if entry.uaa_available_for_preview
        ),
        blocked_authority_refs=[
            "blocked-authority:runtime-tool-registry-invocation",
            "blocked-authority:runtime-tool-registry-execution",
            "blocked-authority:runtime-tool-registry-remote-discovery",
            "blocked-authority:runtime-command-execution-without-gateway-allowlist",
            "blocked-authority:runtime-unrestricted-command-execution",
            "blocked-authority:runtime-browser-automation",
            "blocked-authority:runtime-web-fetch-without-gateway",
            "blocked-authority:runtime-connector-write",
            "blocked-authority:runtime-plugin-import",
            "blocked-authority:runtime-remote-provider-model-call",
            "blocked-authority:runtime-production-authority",
        ],
        proof_refs=[
            RUNTIME_TOOL_REGISTRY_PROOF_REF,
            "proof-ref:runtime-tool-registry:uaa-native-catalog-bridged",
            "proof-ref:runtime-tool-registry:zero-invocation-authority",
        ],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-10"],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-tool-registry:bind-per-tool-approval",
            "next-safe-action-ref:runtime-tool-registry:add-idempotent-receipts",
            "next-safe-action-ref:runtime-tool-registry:add-safe-disable-and-rollback",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_TOOL_REGISTRY_AUTHORITY_MAPPING_MISSING")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
