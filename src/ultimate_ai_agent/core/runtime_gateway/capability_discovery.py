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
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + ["runtime_payload_omitted"]
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
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_CONTROL_CENTER_DIRECT_DENIED")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_SAFE_REFS_REQUIRED")
        if self.uaa_authorized_capability_count != 0:
            raise ValueError("RUNTIME_CAPABILITY_DISCOVERY_AUTHORIZED_COUNT_DENIED")
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


def _snapshot_hash_ref(groups: list[RuntimeDiscoveredCapabilityGroup]) -> str:
    payload = {
        "contract_ref": RUNTIME_CAPABILITY_DISCOVERY_CONTRACT_REF,
        "snapshot_ref": RUNTIME_CAPABILITY_DISCOVERY_SNAPSHOT_REF,
        "groups": [group.model_dump(mode="json") for group in groups],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-capability-discovery:{digest[:16]}"


def build_runtime_capability_discovery_read_model() -> RuntimeCapabilityDiscoveryReadModel:
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
                "Runtime toolsets remain untrusted metadata until UAA maps exact "
                "tools to policy, approval, receipt, and rollback posture."
            ),
            capability_refs=["capability-ref:runtime-discovery:toolsets"],
            blocked_authority_refs=[
                "blocked-authority:runtime-command-execution-without-gateway-allowlist",
                "blocked-authority:runtime-unrestricted-command-execution",
            ],
            next_safe_action_refs=[
                "next-safe-action-ref:runtime-discovery:map-toolset-policy"
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
        snapshot_hash_ref=_snapshot_hash_ref(groups),
        capability_groups=groups,
        runtime_supported_capability_count=sum(
            1 for group in groups if group.runtime_supported_by_reference
        ),
        blocked_authority_refs=[
            *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
            "blocked-authority:runtime-background-autonomy",
            "blocked-authority:runtime-capability-cannot-grant-permission",
            "blocked-authority:runtime-capability-stale-or-unreachable",
        ],
        proof_refs=[
            "proof-ref:runtime-capability-discovery:backend-owned-read-model",
            "proof-ref:runtime-capability-discovery:uaa-authority-owner",
            "proof-ref:runtime-capability-discovery:static-snapshot-hash",
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-capability-discovery:add-signed-live-snapshot",
            "next-safe-action-ref:runtime-capability-discovery:add-freshness-policy",
            "next-safe-action-ref:runtime-capability-discovery:evaluate-policy-before-controls",
        ],
    )
