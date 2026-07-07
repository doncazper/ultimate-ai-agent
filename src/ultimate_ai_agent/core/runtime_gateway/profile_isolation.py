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
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    GOVERNED_RUNTIME_REDACTIONS,
    GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
)
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_PROFILE_ISOLATION_CONTRACT_REF = (
    "contract-ref:runtime-profile-isolation:v1"
)
RUNTIME_PROFILE_ISOLATION_ROUTE_REF = "GET /api/runtime/profiles"
RUNTIME_PROFILE_ISOLATION_CLI_REF = "uaa runtime inspect-profiles"
RUNTIME_PROFILE_ISOLATION_PROOF_REF = "proof-ref:runtime-profile-isolation:phase-06"
RUNTIME_PROFILE_ISOLATION_SNAPSHOT_REF = (
    "runtime-profile-isolation-snapshot-ref:uaa:metadata-only"
)
RUNTIME_PROFILE_ISOLATION_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_PROFILE_ISOLATION_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_PROFILE_ISOLATION_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-profile-isolation-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}


class RuntimeProfileRole(str, Enum):
    coding = "coding"
    research = "research"
    operations = "operations"
    crm = "crm"
    review = "review"


class RuntimeProfileConfiguredStatus(str, Enum):
    metadata_configured = "metadata_configured"
    not_configured = "not_configured"
    planned_disabled = "planned_disabled"
    blocked = "blocked"


class RuntimeProfileAuthorityPosture(str, Enum):
    sealed = "sealed"
    read_only_proposal = "read_only_proposal"
    approval_required_future_lane = "approval_required_future_lane"


class RuntimeProfileHealth(str, Enum):
    healthy_metadata_only = "healthy_metadata_only"
    unconfigured_blocked = "unconfigured_blocked"
    planned_blocked = "planned_blocked"
    needs_operator_review = "needs_operator_review"


class RuntimeProfileIsolationRecord(BaseModel):
    profile_ref: str
    delegated_runtime_profile_ref: str
    display_label: str
    role: RuntimeProfileRole
    configured_status: RuntimeProfileConfiguredStatus
    authority_profile: RuntimeProfileAuthorityPosture
    authority_profile_ref: str
    workspace_scope_ref: str
    memory_scope_ref: str
    toolset_posture: str
    profile_health: RuntimeProfileHealth
    isolated_from_profile_refs: list[str] = Field(default_factory=list)
    configured_for_live_runtime: bool = False
    can_create_runtime_profile: bool = False
    can_delete_runtime_profile: bool = False
    can_write_runtime_config: bool = False
    can_copy_sensitive_material: bool = False
    can_change_runtime_defaults: bool = False
    can_execute_tools: bool = False
    can_call_models: bool = False
    can_write_memory: bool = False
    can_access_workspace_paths: bool = False
    cross_profile_authority_bleed_allowed: bool = False
    safe_summary: str
    blocked_reason_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_record(self) -> "RuntimeProfileIsolationRecord":
        for value, field_name in [
            (self.profile_ref, "profile_ref"),
            (self.delegated_runtime_profile_ref, "delegated_runtime_profile_ref"),
            (self.authority_profile_ref, "authority_profile_ref"),
            (self.workspace_scope_ref, "workspace_scope_ref"),
            (self.memory_scope_ref, "memory_scope_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (self.toolset_posture, "toolset_posture"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "isolated_from_profile_refs",
            "blocked_reason_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        denied_flags = {
            "configured_for_live_runtime": self.configured_for_live_runtime,
            "can_create_runtime_profile": self.can_create_runtime_profile,
            "can_delete_runtime_profile": self.can_delete_runtime_profile,
            "can_write_runtime_config": self.can_write_runtime_config,
            "can_copy_sensitive_material": self.can_copy_sensitive_material,
            "can_change_runtime_defaults": self.can_change_runtime_defaults,
            "can_execute_tools": self.can_execute_tools,
            "can_call_models": self.can_call_models,
            "can_write_memory": self.can_write_memory,
            "can_access_workspace_paths": self.can_access_workspace_paths,
            "cross_profile_authority_bleed_allowed": (
                self.cross_profile_authority_bleed_allowed
            ),
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PROFILE_ISOLATION_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeProfileIsolationReadModel(BaseModel):
    schema_version: str = "runtime_profile_isolation.v1"
    contract_ref: str = RUNTIME_PROFILE_ISOLATION_CONTRACT_REF
    snapshot_ref: str = RUNTIME_PROFILE_ISOLATION_SNAPSHOT_REF
    snapshot_hash_ref: str
    route_ref: str = RUNTIME_PROFILE_ISOLATION_ROUTE_REF
    cli_ref: str = RUNTIME_PROFILE_ISOLATION_CLI_REF
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
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    status: str = "profile_metadata_read_model_only"
    default_uaa_profile_ref: str = "runtime-profile-ref:uaa:sealed-default"
    profiles: list[RuntimeProfileIsolationRecord]
    profile_count: int
    configured_profile_count: int
    blocked_profile_count: int
    uaa_profile_refs_separate_from_delegated_runtime_refs: bool = True
    profile_creation_enabled: bool = False
    profile_deletion_enabled: bool = False
    runtime_config_write_enabled: bool = False
    sensitive_material_copy_enabled: bool = False
    runtime_default_change_enabled: bool = False
    cross_profile_authority_bleed_allowed: bool = False
    control_center_mints_profiles: bool = False
    safe_refs_only: bool = True
    raw_profile_names_persisted: bool = False
    raw_workspace_paths_persisted: bool = False
    raw_sensitive_material_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Runtime profiles are represented as isolated UAA-owned metadata refs; "
        "profile creation, config writes, default changes, and sensitive material "
        "copying remain blocked."
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "runtime_profile_names_omitted",
            "workspace_paths_omitted",
            "sensitive_material_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeProfileIsolationReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.default_uaa_profile_ref, "default_uaa_profile_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
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
            (self.status, "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        if self.authority_state_mapping_ref != RUNTIME_PROFILE_ISOLATION_AUTHORITY_MAPPING_REF:
            raise ValueError("RUNTIME_PROFILE_ISOLATION_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_PROFILE_ISOLATION_AUTHORITY_DECISION_INVALID")
        if self.profile_count != len(self.profiles):
            raise ValueError("RUNTIME_PROFILE_ISOLATION_PROFILE_COUNT_DRIFT")
        if self.configured_profile_count != len(
            [
                profile
                for profile in self.profiles
                if profile.configured_status
                == RuntimeProfileConfiguredStatus.metadata_configured.value
            ]
        ):
            raise ValueError("RUNTIME_PROFILE_ISOLATION_CONFIGURED_COUNT_DRIFT")
        if self.blocked_profile_count != len(
            [
                profile
                for profile in self.profiles
                if profile.configured_status
                != RuntimeProfileConfiguredStatus.metadata_configured.value
            ]
        ):
            raise ValueError("RUNTIME_PROFILE_ISOLATION_BLOCKED_COUNT_DRIFT")
        profile_refs = [profile.profile_ref for profile in self.profiles]
        delegated_refs = [
            profile.delegated_runtime_profile_ref for profile in self.profiles
        ]
        if len(profile_refs) != len(set(profile_refs)):
            raise ValueError("RUNTIME_PROFILE_ISOLATION_DUPLICATE_UAA_PROFILE_REF")
        if set(profile_refs) & set(delegated_refs):
            raise ValueError("RUNTIME_PROFILE_ISOLATION_REF_BLEED_DETECTED")
        denied_flags = {
            "profile_creation_enabled": self.profile_creation_enabled,
            "profile_deletion_enabled": self.profile_deletion_enabled,
            "runtime_config_write_enabled": self.runtime_config_write_enabled,
            "sensitive_material_copy_enabled": self.sensitive_material_copy_enabled,
            "runtime_default_change_enabled": self.runtime_default_change_enabled,
            "cross_profile_authority_bleed_allowed": (
                self.cross_profile_authority_bleed_allowed
            ),
            "control_center_mints_profiles": self.control_center_mints_profiles,
            "raw_profile_names_persisted": self.raw_profile_names_persisted,
            "raw_workspace_paths_persisted": self.raw_workspace_paths_persisted,
            "raw_sensitive_material_persisted": self.raw_sensitive_material_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_PROFILE_ISOLATION_MUTATION_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        if not self.uaa_profile_refs_separate_from_delegated_runtime_refs:
            raise ValueError("RUNTIME_PROFILE_ISOLATION_SEPARATE_REFS_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("RUNTIME_PROFILE_ISOLATION_SAFE_REFS_REQUIRED")
        return self


def _profile_record(
    role: RuntimeProfileRole,
    *,
    configured_status: RuntimeProfileConfiguredStatus,
    authority_profile: RuntimeProfileAuthorityPosture,
    health: RuntimeProfileHealth,
    toolset_posture: str,
    summary: str,
) -> RuntimeProfileIsolationRecord:
    slug = role.value
    blocked_refs = [
        f"blocked-authority:runtime-profile-{slug}-create-delete",
        f"blocked-authority:runtime-profile-{slug}-config-write",
        f"blocked-authority:runtime-profile-{slug}-sensitive-material-copy",
        f"blocked-authority:runtime-profile-{slug}-default-change",
        f"blocked-authority:runtime-profile-{slug}-cross-profile-authority",
    ]
    return RuntimeProfileIsolationRecord(
        profile_ref=f"runtime-profile-ref:uaa:{slug}",
        delegated_runtime_profile_ref=f"delegated-profile-ref:hermes:{slug}",
        display_label=f"{role.value.title()} profile",
        role=role,
        configured_status=configured_status,
        authority_profile=authority_profile,
        authority_profile_ref=f"authority-profile-ref:runtime:{slug}:{authority_profile.value}",
        workspace_scope_ref=f"workspace-scope-ref:runtime-profile:{slug}:safe-refs-only",
        memory_scope_ref=f"memory-scope-ref:runtime-profile:{slug}:review-only",
        toolset_posture=toolset_posture,
        profile_health=health,
        safe_summary=summary,
        blocked_reason_refs=blocked_refs,
        proof_refs=[f"proof-ref:runtime-profile-isolation:{slug}"],
        next_safe_action_refs=[
            f"next-safe-action-ref:runtime-profile-isolation:{slug}:define-storage-contract",
            f"next-safe-action-ref:runtime-profile-isolation:{slug}:bind-operator-approval",
        ],
    )


def build_runtime_profile_isolation_read_model() -> RuntimeProfileIsolationReadModel:
    authority_entry = _authority_entry(authority_decision_catalog=None)
    return build_runtime_profile_isolation_read_model_from_authority_catalog(
        authority_decision_catalog=[authority_entry]
    )


def build_runtime_profile_isolation_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeProfileIsolationReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    profiles = [
        _profile_record(
            RuntimeProfileRole.coding,
            configured_status=RuntimeProfileConfiguredStatus.metadata_configured,
            authority_profile=RuntimeProfileAuthorityPosture.read_only_proposal,
            health=RuntimeProfileHealth.healthy_metadata_only,
            toolset_posture="coding tools metadata only; execution blocked",
            summary="Coding profile is metadata-only and cannot edit files or run tools.",
        ),
        _profile_record(
            RuntimeProfileRole.research,
            configured_status=RuntimeProfileConfiguredStatus.planned_disabled,
            authority_profile=RuntimeProfileAuthorityPosture.sealed,
            health=RuntimeProfileHealth.planned_blocked,
            toolset_posture="research tools planned; web fetch blocked",
            summary="Research profile is planned and cannot fetch web or call providers.",
        ),
        _profile_record(
            RuntimeProfileRole.operations,
            configured_status=RuntimeProfileConfiguredStatus.not_configured,
            authority_profile=RuntimeProfileAuthorityPosture.sealed,
            health=RuntimeProfileHealth.unconfigured_blocked,
            toolset_posture="operations tools unconfigured; execution blocked",
            summary="Operations profile is unconfigured and cannot run local commands.",
        ),
        _profile_record(
            RuntimeProfileRole.crm,
            configured_status=RuntimeProfileConfiguredStatus.not_configured,
            authority_profile=RuntimeProfileAuthorityPosture.sealed,
            health=RuntimeProfileHealth.unconfigured_blocked,
            toolset_posture="CRM connector tools unconfigured; writes blocked",
            summary="CRM profile is unconfigured and cannot sync accounts or write connectors.",
        ),
        _profile_record(
            RuntimeProfileRole.review,
            configured_status=RuntimeProfileConfiguredStatus.metadata_configured,
            authority_profile=RuntimeProfileAuthorityPosture.read_only_proposal,
            health=RuntimeProfileHealth.healthy_metadata_only,
            toolset_posture="review tools metadata only; execution blocked",
            summary="Review profile can be displayed as proposal metadata only.",
        ),
    ]
    blocked_refs = [
        *GOVERNED_RUNTIME_REQUIRED_BLOCKED_AUTHORITY_REFS,
        "blocked-authority:runtime-profile-create-delete",
        "blocked-authority:runtime-profile-config-write",
        "blocked-authority:runtime-profile-sensitive-material-copy",
        "blocked-authority:runtime-profile-default-change",
        "blocked-authority:runtime-profile-cross-profile-authority",
    ]
    return RuntimeProfileIsolationReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(profiles, authority_entry),
        authority_state_route_ref=RUNTIME_PROFILE_ISOLATION_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_PROFILE_ISOLATION_AUTHORITY_STATE_CLI_REF,
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
        profiles=profiles,
        profile_count=len(profiles),
        configured_profile_count=len(
            [
                profile
                for profile in profiles
                if profile.configured_status
                == RuntimeProfileConfiguredStatus.metadata_configured.value
            ]
        ),
        blocked_profile_count=len(
            [
                profile
                for profile in profiles
                if profile.configured_status
                != RuntimeProfileConfiguredStatus.metadata_configured.value
            ]
        ),
        blocked_authority_refs=blocked_refs,
        proof_refs=[
            RUNTIME_PROFILE_ISOLATION_PROOF_REF,
            *[proof for profile in profiles for proof in profile.proof_refs],
        ],
        next_safe_action_refs=[
            "next-safe-action-ref:runtime-profile-isolation:add-profile-storage-contract",
            "next-safe-action-ref:runtime-profile-isolation:add-operator-approval",
            "next-safe-action-ref:runtime-profile-isolation:add-safe-disable-receipts",
            "next-safe-action-ref:runtime-profile-isolation:add-cli-audit-receipts",
        ],
    )


def _snapshot_hash_ref(
    profiles: list[RuntimeProfileIsolationRecord],
    authority_entry: AuthorityDecisionCatalogEntry,
) -> str:
    payload = {
        "contract_ref": RUNTIME_PROFILE_ISOLATION_CONTRACT_REF,
        "snapshot_ref": RUNTIME_PROFILE_ISOLATION_SNAPSHOT_REF,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
        "profiles": [profile.model_dump(mode="json") for profile in profiles],
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return f"snapshot-hash-ref:runtime-profile-isolation:{digest[:16]}"


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_PROFILE_ISOLATION_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_PROFILE_ISOLATION_AUTHORITY_MAPPING_MISSING")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
