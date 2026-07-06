from __future__ import annotations

import hashlib
import json
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


RUNTIME_CAPABILITY_DISCOVERY_CONTRACT_REF = (
    "contract-ref:runtime-capability-discovery:v1"
)
RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF = "GET /api/runtime/capability-discovery"
RUNTIME_CAPABILITY_DISCOVERY_CLI_REF = "uaa runtime inspect-capability-discovery"
RUNTIME_CAPABILITY_DISCOVERY_SNAPSHOT_REF = (
    "capability-snapshot-ref:runtime-discovery:hermes-agent:static-readiness"
)


class RuntimeCapabilityGroupKind(str, Enum):
    models = "models"
    runs = "runs"
    events = "events"
    approvals = "approvals"
    sessions = "sessions"
    skills = "skills"
    toolsets = "toolsets"
    jobs = "jobs"
    blocked_actions = "blocked_actions"


class RuntimeCapabilitySupportStatus(str, Enum):
    reference_only_unverified = "reference_only_unverified"
    unknown_unreachable = "unknown_unreachable"
    planned_disabled = "planned_disabled"
    blocked_by_uaa = "blocked_by_uaa"


class RuntimeCapabilityAuthorizationStatus(str, Enum):
    read_model_only = "read_model_only"
    blocked = "blocked"
    approval_required_future_lane = "approval_required_future_lane"


class RuntimeToolsetSupportStatus(str, Enum):
    runtime_supported_by_reference = "runtime_supported_by_reference"
    runtime_configured_metadata_only = "runtime_configured_metadata_only"
    runtime_planned_disabled = "runtime_planned_disabled"
    runtime_unsupported = "runtime_unsupported"
    runtime_blocked_by_uaa = "runtime_blocked_by_uaa"


class RuntimeToolsetUaaAllowanceStatus(str, Enum):
    enabled_read_only = "enabled_read_only"
    configured_metadata_only = "configured_metadata_only"
    approval_required_future_lane = "approval_required_future_lane"
    blocked = "blocked"
    unsupported = "unsupported"


class RuntimeToolsetSideEffectClass(str, Enum):
    read_only_metadata = "read_only_metadata"
    local_workspace = "local_workspace"
    external_mutation = "external_mutation"
    high_authority = "high_authority"
    unsupported = "unsupported"


class RuntimeDiscoveredCapabilityGroup(BaseModel):
    group_ref: str
    group_kind: RuntimeCapabilityGroupKind
    runtime_support_status: RuntimeCapabilitySupportStatus
    uaa_authorization_status: RuntimeCapabilityAuthorizationStatus
    runtime_supported_by_reference: bool = False
    uaa_authorized_for_execution: bool = False
    stale_or_unreachable_degrades_to_blocked: bool = True
    trust_label: str = "runtime capability is unverified metadata"
    safe_summary: str
    capability_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_group(self) -> "RuntimeDiscoveredCapabilityGroup":
        validate_execution_ref(self.group_ref, "group_ref")
        for field_name in (
            "capability_refs",
            "blocked_authority_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.trust_label, "trust_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.uaa_authorized_for_execution:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_EXECUTION_AUTHORITY_DENIED")
        if not self.stale_or_unreachable_degrades_to_blocked:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_STALE_BLOCK_REQUIRED")
        return self


class RuntimeToolsetCapabilityRecord(BaseModel):
    toolset_ref: str
    display_label: str
    runtime_ref: str = "runtime-identity-ref:hermes-agent:optional-target"
    profile_ref: str
    runtime_support_status: RuntimeToolsetSupportStatus
    uaa_allowance_status: RuntimeToolsetUaaAllowanceStatus
    side_effect_class: RuntimeToolsetSideEffectClass
    authority_mode_ref: str
    approval_scope_ref: str
    safe_disable_ref: str
    receipt_ref: str
    verifier_ref: str
    safe_summary: str
    runtime_supports_toolset: bool = False
    uaa_allows_execution: bool = False
    tool_invocation_enabled: bool = False
    toolset_config_mutation_enabled: bool = False
    hermes_toolset_enablement_enabled: bool = False
    raw_tool_payload_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeToolsetCapabilityRecord":
        for value, field_name in [
            (self.toolset_ref, "toolset_ref"),
            (self.runtime_ref, "runtime_ref"),
            (self.profile_ref, "profile_ref"),
            (self.authority_mode_ref, "authority_mode_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.receipt_ref, "receipt_ref"),
            (self.verifier_ref, "verifier_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("blocked_authority_refs", "next_safe_action_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "uaa_allows_execution": self.uaa_allows_execution,
            "tool_invocation_enabled": self.tool_invocation_enabled,
            "toolset_config_mutation_enabled": self.toolset_config_mutation_enabled,
            "hermes_toolset_enablement_enabled": self.hermes_toolset_enablement_enabled,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_TOOLSET_CAPABILITY_EXECUTION_DENIED: " + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_TOOLSET_CAPABILITY_BLOCKERS_REQUIRED")
        if not self.next_safe_action_refs:
            raise ValueError("RUNTIME_TOOLSET_CAPABILITY_NEXT_ACTION_REQUIRED")
        if (
            self.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.enabled_read_only.value
            and self.side_effect_class
            != RuntimeToolsetSideEffectClass.read_only_metadata.value
        ):
            raise ValueError("RUNTIME_TOOLSET_READ_ONLY_SIDE_EFFECT_REQUIRED")
        if (
            self.side_effect_class == RuntimeToolsetSideEffectClass.high_authority.value
            and "blocked-authority:runtime-high-authority-toolset"
            not in self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_TOOLSET_HIGH_AUTHORITY_BLOCKER_REQUIRED")
        return self


class RuntimeToolsetCapabilityPosture(BaseModel):
    schema_version: str = "runtime_toolset_capability_posture.v1"
    contract_ref: str = "contract-ref:hermes-runtime-toolset-capability-posture:v1"
    status: str = "read_only_toolset_capability_posture"
    route_ref: str = RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF
    cli_ref: str = RUNTIME_CAPABILITY_DISCOVERY_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_profile_ref: str = (
        "authority-profile-ref:runtime-toolsets:read-only-posture"
    )
    safe_summary: str = (
        "UAA maps delegated runtime toolsets as read-only posture metadata; "
        "tool invocation and toolset configuration changes remain blocked."
    )
    records: list[RuntimeToolsetCapabilityRecord]
    toolset_count: int = 0
    runtime_supported_count: int = 0
    uaa_allowed_execution_count: int = 0
    enabled_read_only_count: int = 0
    configured_metadata_only_count: int = 0
    approval_required_future_count: int = 0
    blocked_count: int = 0
    unsupported_count: int = 0
    live_tool_invocation_enabled: bool = False
    toolset_config_mutation_enabled: bool = False
    hermes_toolset_enablement_enabled: bool = False
    raw_tool_payload_persisted: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_posture(self) -> "RuntimeToolsetCapabilityPosture":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_profile_ref, "authority_profile_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
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
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        if not self.records:
            raise ValueError("RUNTIME_TOOLSET_CAPABILITY_RECORDS_REQUIRED")
        expected_toolset_count = len(self.records)
        if self.toolset_count != expected_toolset_count:
            raise ValueError("RUNTIME_TOOLSET_CAPABILITY_COUNT_MISMATCH")
        runtime_supported_count = sum(
            1 for record in self.records if record.runtime_supports_toolset
        )
        if self.runtime_supported_count != runtime_supported_count:
            raise ValueError("RUNTIME_TOOLSET_RUNTIME_SUPPORTED_COUNT_MISMATCH")
        uaa_allowed_execution_count = sum(
            1 for record in self.records if record.uaa_allows_execution
        )
        if self.uaa_allowed_execution_count != uaa_allowed_execution_count:
            raise ValueError("RUNTIME_TOOLSET_UAA_EXECUTION_COUNT_MISMATCH")
        if self.uaa_allowed_execution_count != 0:
            raise ValueError("RUNTIME_TOOLSET_UAA_EXECUTION_COUNT_DENIED")
        status_counts = {
            RuntimeToolsetUaaAllowanceStatus.enabled_read_only.value: self.enabled_read_only_count,
            RuntimeToolsetUaaAllowanceStatus.configured_metadata_only.value: self.configured_metadata_only_count,
            RuntimeToolsetUaaAllowanceStatus.approval_required_future_lane.value: self.approval_required_future_count,
            RuntimeToolsetUaaAllowanceStatus.blocked.value: self.blocked_count,
            RuntimeToolsetUaaAllowanceStatus.unsupported.value: self.unsupported_count,
        }
        for status, expected_count in status_counts.items():
            actual_count = sum(
                1 for record in self.records if record.uaa_allowance_status == status
            )
            if expected_count != actual_count:
                raise ValueError("RUNTIME_TOOLSET_ALLOWANCE_COUNT_MISMATCH")
        denied_flags = {
            "live_tool_invocation_enabled": self.live_tool_invocation_enabled,
            "toolset_config_mutation_enabled": self.toolset_config_mutation_enabled,
            "hermes_toolset_enablement_enabled": self.hermes_toolset_enablement_enabled,
            "raw_tool_payload_persisted": self.raw_tool_payload_persisted,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_TOOLSET_CAPABILITY_POSTURE_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_TOOLSET_CAPABILITY_POSTURE_BLOCKERS_REQUIRED")
        return self


class RuntimeCapabilityDiscoveryReadModel(BaseModel):
    schema_version: str = "runtime_capability_discovery.v1"
    contract_ref: str = RUNTIME_CAPABILITY_DISCOVERY_CONTRACT_REF
    snapshot_ref: str = RUNTIME_CAPABILITY_DISCOVERY_SNAPSHOT_REF
    snapshot_hash_ref: str
    runtime_identity_ref: str = "runtime-identity-ref:hermes-agent:optional-target"
    adapter_ref: str = "runtime-delegation-adapter:hermes-agent"
    runtime_label: str = "Hermes Agent optional delegated runtime"
    status: str = "static_readiness_only"
    freshness_status: str = "static_snapshot_unverified"
    runtime_reachable: bool = False
    live_discovery_performed: bool = False
    stale: bool = True
    stale_or_unreachable_degrades_to_blocked: bool = True
    runtime_supported_cannot_grant_uaa_permission: bool = True
    uaa_controls_authority: bool = True
    control_center_talks_directly_to_runtime: bool = False
    route_ref: str = RUNTIME_CAPABILITY_DISCOVERY_ROUTE_REF
    cli_ref: str = RUNTIME_CAPABILITY_DISCOVERY_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    freshness_policy_ref: str = (
        "freshness-policy-ref:runtime-capability-discovery:live-snapshot-required"
    )
    policy_evaluation_ref: str = (
        "policy-evaluation-ref:runtime-capability-discovery:blocked-by-default"
    )
    capability_groups: list[RuntimeDiscoveredCapabilityGroup]
    toolset_posture: RuntimeToolsetCapabilityPosture
    runtime_supported_capability_count: int = 0
    uaa_authorized_capability_count: int = 0
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    raw_runtime_payload_persisted: bool = False
    raw_log_persisted: bool = False
    raw_local_path_persisted: bool = False
    credential_material_persisted: bool = False
    safe_summary: str = (
        "Runtime capability discovery is a static backend-owned readiness "
        "snapshot; UAA authority remains blocked unless exact lanes graduate."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS) + ["runtime_payload_omitted"]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeCapabilityDiscoveryReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.runtime_identity_ref, "runtime_identity_ref"),
            (self.adapter_ref, "adapter_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.freshness_policy_ref, "freshness_policy_ref"),
            (self.policy_evaluation_ref, "policy_evaluation_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.runtime_label, "runtime_label"),
            (self.status, "status"),
            (self.freshness_status, "freshness_status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        for redaction in self.redactions_applied:
            validate_safe_execution_text(redaction, "redactions_applied")
        expected_groups = {kind.value for kind in RuntimeCapabilityGroupKind}
        actual_groups = {group.group_kind for group in self.capability_groups}
        if actual_groups != expected_groups:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_GROUPS_INCOMPLETE")
        if self.runtime_reachable or self.live_discovery_performed:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_LIVE_CALL_DENIED")
        if not self.stale or not self.stale_or_unreachable_degrades_to_blocked:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_STALE_BLOCK_REQUIRED")
        if not self.runtime_supported_cannot_grant_uaa_permission:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_PERMISSION_GRANT_DENIED")
        if not self.uaa_controls_authority:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_UAA_AUTHORITY_REQUIRED")
        if self.control_center_talks_directly_to_runtime:
            raise ValueError(
                "RUNTIME_CAPABILITY_DISCOVERY_CONTROL_CENTER_DIRECT_DENIED"
            )
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_SAFE_REFS_REQUIRED")
        if self.uaa_authorized_capability_count != 0:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_AUTHORIZED_COUNT_DENIED")
        if self.toolset_posture.uaa_allowed_execution_count != 0:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_TOOLSET_EXECUTION_DENIED")
        if self.toolset_posture.live_tool_invocation_enabled:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_TOOL_INVOCATION_DENIED")
        if self.toolset_posture.toolset_config_mutation_enabled:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_TOOLSET_CONFIG_DENIED")
        denied_flags = {
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "raw_runtime_payload_persisted": self.raw_runtime_payload_persisted,
            "raw_log_persisted": self.raw_log_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "credential_material_persisted": self.credential_material_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CAPABILITY_DISCOVERY_RAW_PERSISTENCE_DENIED: "
                + ", ".join(enabled)
            )
        return self


def _capability_group(
    kind: RuntimeCapabilityGroupKind,
    *,
    runtime_supported_by_reference: bool,
    runtime_support_status: RuntimeCapabilitySupportStatus,
    uaa_authorization_status: RuntimeCapabilityAuthorizationStatus,
    safe_summary: str,
    capability_refs: list[str],
    blocked_authority_refs: list[str],
    next_safe_action_refs: list[str],
) -> RuntimeDiscoveredCapabilityGroup:
    dashed = kind.value.replace("_", "-")
    return RuntimeDiscoveredCapabilityGroup(
        group_ref=f"capability-group-ref:runtime-discovery:{dashed}",
        group_kind=kind,
        runtime_support_status=runtime_support_status,
        uaa_authorization_status=uaa_authorization_status,
        runtime_supported_by_reference=runtime_supported_by_reference,
        safe_summary=safe_summary,
        capability_refs=capability_refs,
        blocked_authority_refs=blocked_authority_refs,
        next_safe_action_refs=next_safe_action_refs,
    )


def _toolset_record(
    *,
    slug: str,
    display_label: str,
    profile_ref: str,
    runtime_support_status: RuntimeToolsetSupportStatus,
    uaa_allowance_status: RuntimeToolsetUaaAllowanceStatus,
    side_effect_class: RuntimeToolsetSideEffectClass,
    runtime_supports_toolset: bool,
    safe_summary: str,
    blocked_authority_refs: list[str],
    next_safe_action_refs: list[str],
) -> RuntimeToolsetCapabilityRecord:
    return RuntimeToolsetCapabilityRecord(
        toolset_ref=f"toolset-ref:runtime:{slug}",
        display_label=display_label,
        profile_ref=profile_ref,
        runtime_support_status=runtime_support_status,
        uaa_allowance_status=uaa_allowance_status,
        side_effect_class=side_effect_class,
        authority_mode_ref="authority-mode-ref:runtime-toolsets:read-only-posture",
        approval_scope_ref=f"approval-scope-ref:runtime-toolset:{slug}:future",
        safe_disable_ref=f"safe-disable-ref:runtime-toolset:{slug}:disabled",
        receipt_ref=f"receipt-ref:runtime-toolset:{slug}:not-executed",
        verifier_ref="verifier-ref:hermes-runtime-adoption:phase-09",
        safe_summary=safe_summary,
        runtime_supports_toolset=runtime_supports_toolset,
        blocked_authority_refs=blocked_authority_refs,
        next_safe_action_refs=next_safe_action_refs,
    )


def _build_runtime_toolset_capability_posture() -> RuntimeToolsetCapabilityPosture:
    records = [
        _toolset_record(
            slug="core-readonly-metadata",
            display_label="Core read-only metadata",
            profile_ref="runtime-profile-ref:hermes:shared-readiness",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_configured_metadata_only,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.enabled_read_only,
            side_effect_class=RuntimeToolsetSideEffectClass.read_only_metadata,
            runtime_supports_toolset=True,
            safe_summary=(
                "UAA can display safe delegated runtime metadata, capability "
                "refs, and blocked-state labels without invoking tools."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-toolset-invocation",
                "blocked-authority:runtime-toolset-config-mutation",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:keep-metadata-read-only"
            ],
        ),
        _toolset_record(
            slug="profile-session-metadata",
            display_label="Profile and session metadata",
            profile_ref="runtime-profile-ref:hermes:shared-readiness",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_configured_metadata_only,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.configured_metadata_only,
            side_effect_class=RuntimeToolsetSideEffectClass.read_only_metadata,
            runtime_supports_toolset=True,
            safe_summary=(
                "UAA records profile and session posture as safe refs only; "
                "it does not create sessions or change runtime defaults."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-session-open-without-transport",
                "blocked-authority:runtime-profile-config-mutation",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:add-signed-profile-snapshot"
            ],
        ),
        _toolset_record(
            slug="coding-workspace",
            display_label="Coding workspace tools",
            profile_ref="runtime-profile-ref:hermes:coding",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_supported_by_reference,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.approval_required_future_lane,
            side_effect_class=RuntimeToolsetSideEffectClass.local_workspace,
            runtime_supports_toolset=True,
            safe_summary=(
                "Coding workspace tools require exact workspace scope, patch "
                "proposal receipts, rollback posture, and approval binding."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-toolset-invocation",
                "blocked-authority:runtime-file-mutation-without-patch-lane",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:define-coding-tool-grant"
            ],
        ),
        _toolset_record(
            slug="command-execution",
            display_label="Command execution tools",
            profile_ref="runtime-profile-ref:hermes:coding",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_supported_by_reference,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.approval_required_future_lane,
            side_effect_class=RuntimeToolsetSideEffectClass.high_authority,
            runtime_supports_toolset=True,
            safe_summary=(
                "Command tools stay blocked until RuntimeGateway can enforce "
                "argv-only allowlists, jailed cwd, timeout, redaction, and receipts."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-high-authority-toolset",
                "blocked-authority:runtime-command-execution-without-gateway-allowlist",
                "blocked-authority:runtime-unrestricted-command-execution",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:bind-command-tool-approval"
            ],
        ),
        _toolset_record(
            slug="web-browser",
            display_label="Browser and web tools",
            profile_ref="runtime-profile-ref:hermes:research",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_planned_disabled,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.blocked,
            side_effect_class=RuntimeToolsetSideEffectClass.high_authority,
            runtime_supports_toolset=False,
            safe_summary=(
                "Browser and web toolsets remain blocked; future work must route "
                "through WebAccessGateway and preserve action blocks."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-high-authority-toolset",
                "blocked-authority:runtime-browser-automation",
                "blocked-authority:runtime-web-fetch-without-gateway",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:define-webaccess-readonly-lane"
            ],
        ),
        _toolset_record(
            slug="connector-write",
            display_label="Connector write tools",
            profile_ref="runtime-profile-ref:hermes:operations",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_planned_disabled,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.blocked,
            side_effect_class=RuntimeToolsetSideEffectClass.external_mutation,
            runtime_supports_toolset=False,
            safe_summary=(
                "Connector write toolsets are blocked until exact connector "
                "draft, approval, send/write, rollback, and receipt lanes exist."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-connector-write",
                "blocked-authority:connector-write-without-exact-lane",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:create-connector-draft-only-review"
            ],
        ),
        _toolset_record(
            slug="plugin-runtime-import",
            display_label="Plugin runtime import tools",
            profile_ref="runtime-profile-ref:hermes:extensions",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_unsupported,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.unsupported,
            side_effect_class=RuntimeToolsetSideEffectClass.unsupported,
            runtime_supports_toolset=False,
            safe_summary=(
                "Runtime plugin imports are unsupported in this posture; "
                "external skills must become reviewed UAA-owned adaptations."
            ),
            blocked_authority_refs=["blocked-authority:runtime-plugin-import"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:add-plugin-adaptation-contract"
            ],
        ),
        _toolset_record(
            slug="production-ops",
            display_label="Production operations tools",
            profile_ref="runtime-profile-ref:hermes:operations",
            runtime_support_status=RuntimeToolsetSupportStatus.runtime_blocked_by_uaa,
            uaa_allowance_status=RuntimeToolsetUaaAllowanceStatus.blocked,
            side_effect_class=RuntimeToolsetSideEffectClass.high_authority,
            runtime_supports_toolset=False,
            safe_summary=(
                "Production operations authority remains blocked and cannot be "
                "granted by delegated runtime capability claims."
            ),
            blocked_authority_refs=[
                "blocked-authority:runtime-high-authority-toolset",
                "blocked-authority:runtime-production-authority",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-toolsets:keep-production-authority-blocked"
            ],
        ),
    ]
    return RuntimeToolsetCapabilityPosture(
        records=records,
        toolset_count=len(records),
        runtime_supported_count=sum(
            1 for record in records if record.runtime_supports_toolset
        ),
        enabled_read_only_count=sum(
            1
            for record in records
            if record.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.enabled_read_only.value
        ),
        configured_metadata_only_count=sum(
            1
            for record in records
            if record.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.configured_metadata_only.value
        ),
        approval_required_future_count=sum(
            1
            for record in records
            if record.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.approval_required_future_lane.value
        ),
        blocked_count=sum(
            1
            for record in records
            if record.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.blocked.value
        ),
        unsupported_count=sum(
            1
            for record in records
            if record.uaa_allowance_status
            == RuntimeToolsetUaaAllowanceStatus.unsupported.value
        ),
        blocked_authority_refs=[
            "blocked-authority:runtime-toolset-invocation",
            "blocked-authority:runtime-toolset-config-mutation",
            "blocked-authority:runtime-toolset-enablement",
            "blocked-authority:runtime-command-execution-without-gateway-allowlist",
            "blocked-authority:runtime-unrestricted-command-execution",
            "blocked-authority:runtime-browser-automation",
            "blocked-authority:runtime-connector-write",
            "blocked-authority:runtime-plugin-import",
            "blocked-authority:runtime-production-authority",
        ],
        proof_refs=[
            "proof-ref:hermes-runtime-adoption:phase-09:toolsets",
            "proof-ref:runtime-toolsets:uaa-allows-zero-execution",
        ],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-09"],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-toolsets:define-exact-toolset-grant",
            "next-safe-action-ref:runtime-toolsets:add-per-tool-side-effect-policy",
            "next-safe-action-ref:runtime-toolsets:bind-approval-receipt-safe-disable",
        ],
    )


def _snapshot_hash_ref(
    groups: list[RuntimeDiscoveredCapabilityGroup],
    toolset_posture: RuntimeToolsetCapabilityPosture,
) -> str:
    payload = {
        "contract_ref": RUNTIME_CAPABILITY_DISCOVERY_CONTRACT_REF,
        "snapshot_ref": RUNTIME_CAPABILITY_DISCOVERY_SNAPSHOT_REF,
        "groups": [group.model_dump(mode="json") for group in groups],
        "toolset_posture": toolset_posture.model_dump(mode="json"),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-capability-discovery:{digest[:16]}"


def build_runtime_capability_discovery_read_model() -> (
    RuntimeCapabilityDiscoveryReadModel
):
    toolset_posture = _build_runtime_toolset_capability_posture()
    groups = [
        _capability_group(
            RuntimeCapabilityGroupKind.models,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "External runtime model support is reference-only and cannot "
                "perform model calls in UAA."
            ),
            capability_refs=["capability-ref:runtime-discovery:models"],
            blocked_authority_refs=[
                "blocked-authority:runtime-remote-provider-model-call",
                "blocked-authority:runtime-capability-model-call-without-lane",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:add-model-metadata-snapshot"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.runs,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime run support is surfaced as readiness metadata only; "
                "UAA cannot start delegated runs yet."
            ),
            capability_refs=["capability-ref:runtime-discovery:runs"],
            blocked_authority_refs=[
                "blocked-authority:runtime-delegation-live-run-submission"
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:define-run-proposal-contract"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.events,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime events need a bounded redacted ingestion lane before "
                "they can become Evidence or Proof refs."
            ),
            capability_refs=["capability-ref:runtime-discovery:events"],
            blocked_authority_refs=[
                "blocked-authority:runtime-live-event-transport-without-lane"
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:add-redacted-event-snapshot"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.approvals,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime approval requests can be represented as UAA envelopes "
                "later, but runtime approval resolution is blocked now."
            ),
            capability_refs=["capability-ref:runtime-discovery:approvals"],
            blocked_authority_refs=[
                "blocked-authority:runtime-approval-resolution-without-envelope"
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:bind-action-inbox-envelope"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.sessions,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime sessions are optional references only; UAA does not "
                "open or resume external sessions in this phase."
            ),
            capability_refs=["capability-ref:runtime-discovery:sessions"],
            blocked_authority_refs=[
                "blocked-authority:runtime-session-open-without-transport"
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:add-session-posture"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.skills,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "External runtime skills are discovery signals only and do not "
                "grant plugin import or execution authority."
            ),
            capability_refs=["capability-ref:runtime-discovery:skills"],
            blocked_authority_refs=["blocked-authority:runtime-plugin-import"],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:add-skill-metadata-review"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.toolsets,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime toolsets now have structured UAA posture metadata, "
                "but invocation and configuration changes remain blocked."
            ),
            capability_refs=[
                "capability-ref:runtime-discovery:toolsets",
                *[record.toolset_ref for record in toolset_posture.records],
            ],
            blocked_authority_refs=toolset_posture.blocked_authority_refs,
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:map-toolset-policy",
                *toolset_posture.next_safe_action_refs,
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.jobs,
            runtime_supported_by_reference=True,
            runtime_support_status=RuntimeCapabilitySupportStatus.reference_only_unverified,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Runtime jobs are not scheduled or started; background autonomy "
                "and remote execution remain blocked."
            ),
            capability_refs=["capability-ref:runtime-discovery:jobs"],
            blocked_authority_refs=[
                "blocked-authority:runtime-background-autonomy",
                "blocked-authority:runtime-remote-execution",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:add-job-readiness-contract"
            ],
        ),
        _capability_group(
            RuntimeCapabilityGroupKind.blocked_actions,
            runtime_supported_by_reference=False,
            runtime_support_status=RuntimeCapabilitySupportStatus.blocked_by_uaa,
            uaa_authorization_status=RuntimeCapabilityAuthorizationStatus.blocked,
            safe_summary=(
                "Browser, connector, shell, remote, provider, plugin, broad "
                "autonomy, and production actions remain blocked."
            ),
            capability_refs=["capability-ref:runtime-discovery:blocked-actions"],
            blocked_authority_refs=[
                *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
                "blocked-authority:runtime-background-autonomy",
                "blocked-authority:runtime-capability-cannot-grant-permission",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:promote-exact-lanes-only"
            ],
        ),
    ]
    return RuntimeCapabilityDiscoveryReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(groups, toolset_posture),
        capability_groups=groups,
        toolset_posture=toolset_posture,
        runtime_supported_capability_count=sum(
            1 for group in groups if group.runtime_supported_by_reference
        ),
        blocked_authority_refs=[
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            "blocked-authority:runtime-background-autonomy",
            "blocked-authority:runtime-capability-cannot-grant-permission",
            "blocked-authority:runtime-capability-stale-or-unreachable",
            *toolset_posture.blocked_authority_refs,
        ],
        proof_refs=[
            "proof-ref:runtime-capability-discovery:backend-owned-read-model",
            "proof-ref:runtime-capability-discovery:uaa-authority-owner",
            "proof-ref:runtime-capability-discovery:static-snapshot-hash",
            *toolset_posture.proof_refs,
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-capability-discovery:add-signed-live-snapshot",
            "next-safe-action-ref:runtime-capability-discovery:add-freshness-policy",
            "next-safe-action-ref:runtime-capability-discovery:evaluate-policy-before-controls",
        ],
    )
