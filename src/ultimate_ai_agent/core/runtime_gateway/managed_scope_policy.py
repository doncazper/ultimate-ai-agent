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
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_MANAGED_SCOPE_POLICY_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-managed-scope-policy:v1"
)
RUNTIME_MANAGED_SCOPE_POLICY_ROUTE_REF = "GET /api/runtime/managed-scope-policy"
RUNTIME_MANAGED_SCOPE_POLICY_CLI_REF = "uaa runtime inspect-managed-scope-policy"
RUNTIME_MANAGED_SCOPE_POLICY_SNAPSHOT_REF = (
    "managed-scope-policy-snapshot-ref:runtime:local-policy-profile"
)
RUNTIME_MANAGED_SCOPE_POLICY_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-27:managed-scope-policy"
)
RUNTIME_MANAGED_SCOPE_POLICY_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-27:managed-scope-policy"
)
RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_ROUTE_REF = (
    "GET /api/runtime/authority-state"
)
RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-managed-scope-policy-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:managed-scope-no-system-config-write",
    "blocked-authority:managed-scope-no-privileged-write",
    "blocked-authority:managed-scope-no-mdm-delivery",
    "blocked-authority:managed-scope-no-protected-material-management",
    "blocked-authority:managed-scope-no-unsigned-runtime-config-override",
    "blocked-authority:managed-scope-no-production-enforcement",
    "blocked-authority:managed-scope-no-control-center-authority-mint",
)


class RuntimeManagedScopePolicySourceKind(str, Enum):
    repo_local_policy = "repo_local_policy"
    prompt_pack_policy = "prompt_pack_policy"
    operator_profile = "operator_profile"
    runtime_default = "runtime_default"


class RuntimeManagedScopeDriftStatus(str, Enum):
    aligned = "aligned"
    warning = "warning"
    blocked = "blocked"


class RuntimeManagedScopePolicyPinSource(BaseModel):
    source_ref: str
    source_kind: RuntimeManagedScopePolicySourceKind
    display_label: str
    precedence: int = Field(..., ge=1)
    pinned: bool = True
    verified: bool = True
    active: bool = True
    checksum_ref: str
    drift_status: RuntimeManagedScopeDriftStatus = RuntimeManagedScopeDriftStatus.aligned
    drift_warning_ref: str | None = None
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    system_config_write_performed: bool = False
    privileged_write_performed: bool = False
    mdm_delivery_performed: bool = False
    managed_protected_material_performed: bool = False
    unsigned_runtime_config_override_performed: bool = False
    production_enforcement_claimed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_pin_source(self) -> "RuntimeManagedScopePolicyPinSource":
        for value, field_name in [
            (self.source_ref, "source_ref"),
            (self.checksum_ref, "checksum_ref"),
        ]:
            validate_execution_ref(value, field_name)
        if self.drift_warning_ref is not None:
            validate_execution_ref(self.drift_warning_ref, "drift_warning_ref")
        for ref in self.blocked_authority_refs:
            validate_execution_ref(ref, "blocked_authority_refs")
        for value, field_name in [
            (str(self.source_kind), "source_kind"),
            (self.display_label, "display_label"),
            (str(self.drift_status), "drift_status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if not self.pinned or not self.verified:
            raise ValueError("RUNTIME_MANAGED_SCOPE_PIN_VERIFICATION_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_MANAGED_SCOPE_PIN_BLOCKERS_REQUIRED")
        if self.drift_status != RuntimeManagedScopeDriftStatus.aligned.value:
            if self.drift_warning_ref is None:
                raise ValueError("RUNTIME_MANAGED_SCOPE_DRIFT_WARNING_REF_REQUIRED")
        denied_flags = {
            "system_config_write_performed": self.system_config_write_performed,
            "privileged_write_performed": self.privileged_write_performed,
            "mdm_delivery_performed": self.mdm_delivery_performed,
            "managed_protected_material_performed": (
                self.managed_protected_material_performed
            ),
            "unsigned_runtime_config_override_performed": (
                self.unsigned_runtime_config_override_performed
            ),
            "production_enforcement_claimed": self.production_enforcement_claimed,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_MANAGED_SCOPE_PIN_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeManagedScopePolicyDriftWarning(BaseModel):
    warning_ref: str
    source_ref: str
    status: RuntimeManagedScopeDriftStatus
    severity: str
    safe_summary: str
    expected_policy_ref: str
    observed_policy_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    operator_review_required: bool = True
    auto_remediation_performed: bool = False
    runtime_config_write_performed: bool = False
    unsigned_override_accepted: bool = False
    production_enforcement_claimed: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_warning(self) -> "RuntimeManagedScopePolicyDriftWarning":
        for value, field_name in [
            (self.warning_ref, "warning_ref"),
            (self.source_ref, "source_ref"),
            (self.expected_policy_ref, "expected_policy_ref"),
            (self.observed_policy_ref, "observed_policy_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("blocked_authority_refs", "proof_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (str(self.status), "status"),
            (self.severity, "severity"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.operator_review_required is not True:
            raise ValueError("RUNTIME_MANAGED_SCOPE_OPERATOR_REVIEW_REQUIRED")
        if not self.blocked_authority_refs or not self.proof_refs:
            raise ValueError("RUNTIME_MANAGED_SCOPE_DRIFT_EVIDENCE_REQUIRED")
        denied_flags = {
            "auto_remediation_performed": self.auto_remediation_performed,
            "runtime_config_write_performed": self.runtime_config_write_performed,
            "unsigned_override_accepted": self.unsigned_override_accepted,
            "production_enforcement_claimed": self.production_enforcement_claimed,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_MANAGED_SCOPE_DRIFT_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        return self


class RuntimeManagedScopePolicyReadModel(BaseModel):
    schema_version: str = "runtime_managed_scope_policy.v1"
    contract_ref: str = RUNTIME_MANAGED_SCOPE_POLICY_CONTRACT_REF
    status: str = "read_only_local_policy_profile_posture"
    snapshot_ref: str = RUNTIME_MANAGED_SCOPE_POLICY_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-managed-scope:pending"
    route_ref: str = RUNTIME_MANAGED_SCOPE_POLICY_ROUTE_REF
    cli_ref: str = RUNTIME_MANAGED_SCOPE_POLICY_CLI_REF
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
    policy_profile_ref: str = "managed-policy-profile-ref:runtime:local-operator"
    profile_label: str = "Local Operator Governed Runtime"
    safe_summary: str = (
        "Managed scope policy shows local pinned defaults and drift warnings "
        "without writing system config."
    )
    pinned_sources: list[RuntimeManagedScopePolicyPinSource] = Field(
        default_factory=list
    )
    drift_warnings: list[RuntimeManagedScopePolicyDriftWarning] = Field(
        default_factory=list
    )
    pinned_source_count: int = 0
    active_pinned_source_count: int = 0
    drift_warning_count: int = 0
    blocked_drift_warning_count: int = 0
    local_config_source_visible: bool = True
    precedence_visible: bool = True
    verification_visible: bool = True
    rollback_ref: str = "rollback-ref:managed-scope-policy:restore-local-profile"
    admin_operator_proof_ref: str = RUNTIME_MANAGED_SCOPE_POLICY_PROOF_REF
    system_config_write_enabled: bool = False
    privileged_write_enabled: bool = False
    mdm_delivery_enabled: bool = False
    managed_secrets_enabled: bool = False
    unsigned_runtime_config_override_enabled: bool = False
    production_enforcement_claimed: bool = False
    control_center_mints_authority: bool = False
    runtime_config_mutation_performed: bool = False
    raw_config_persisted: bool = False
    raw_local_path_persisted: bool = False
    account_material_persisted: bool = False
    credential_material_persisted: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_config_omitted",
            "raw_path_omitted",
            "protected_material_omitted",
            "account_material_omitted",
        ]
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeManagedScopePolicyReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
            (self.policy_profile_ref, "policy_profile_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.admin_operator_proof_ref, "admin_operator_proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
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
            (self.profile_label, "profile_label"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "redactions_applied",
        ):
            for value in getattr(self, field_name):
                if field_name == "redactions_applied":
                    validate_safe_execution_text(value, field_name)
                else:
                    validate_execution_ref(value, field_name)
        if (
            self.authority_state_mapping_ref
            != RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_MANAGED_SCOPE_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_MANAGED_SCOPE_AUTHORITY_DECISION_INVALID")
        if self.pinned_source_count != len(self.pinned_sources):
            raise ValueError("RUNTIME_MANAGED_SCOPE_PIN_COUNT_DRIFT")
        if self.active_pinned_source_count != sum(
            1 for source in self.pinned_sources if source.active
        ):
            raise ValueError("RUNTIME_MANAGED_SCOPE_ACTIVE_PIN_COUNT_DRIFT")
        if self.drift_warning_count != len(self.drift_warnings):
            raise ValueError("RUNTIME_MANAGED_SCOPE_DRIFT_COUNT_DRIFT")
        if self.blocked_drift_warning_count != sum(
            1
            for warning in self.drift_warnings
            if warning.status == RuntimeManagedScopeDriftStatus.blocked.value
        ):
            raise ValueError("RUNTIME_MANAGED_SCOPE_BLOCKED_DRIFT_COUNT_DRIFT")
        required_true = {
            "local_config_source_visible": self.local_config_source_visible,
            "precedence_visible": self.precedence_visible,
            "verification_visible": self.verification_visible,
        }
        missing = [name for name, value in required_true.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_MANAGED_SCOPE_VISIBILITY_REQUIRED: " + ", ".join(missing)
            )
        denied_flags = {
            "system_config_write_enabled": self.system_config_write_enabled,
            "privileged_write_enabled": self.privileged_write_enabled,
            "mdm_delivery_enabled": self.mdm_delivery_enabled,
            "managed_secrets_enabled": self.managed_secrets_enabled,
            "unsigned_runtime_config_override_enabled": (
                self.unsigned_runtime_config_override_enabled
            ),
            "production_enforcement_claimed": self.production_enforcement_claimed,
            "control_center_mints_authority": self.control_center_mints_authority,
            "runtime_config_mutation_performed": (
                self.runtime_config_mutation_performed
            ),
            "raw_config_persisted": self.raw_config_persisted,
            "raw_local_path_persisted": self.raw_local_path_persisted,
            "account_material_persisted": self.account_material_persisted,
            "credential_material_persisted": self.credential_material_persisted,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_MANAGED_SCOPE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        for ref in RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS:
            if ref not in self.blocked_authority_refs:
                raise ValueError("RUNTIME_MANAGED_SCOPE_BLOCKER_MISSING")
        if not self.proof_refs or self.admin_operator_proof_ref not in self.proof_refs:
            raise ValueError("RUNTIME_MANAGED_SCOPE_PROOF_REF_REQUIRED")
        return self


def _snapshot_hash_ref(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-managed-scope:{digest}"


def build_runtime_managed_scope_policy_read_model() -> RuntimeManagedScopePolicyReadModel:
    authority_entry = _authority_entry(authority_decision_catalog=None)
    return build_runtime_managed_scope_policy_read_model_from_authority_catalog(
        authority_decision_catalog=[authority_entry]
    )


def build_runtime_managed_scope_policy_read_model_from_authority_catalog(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None = None,
) -> RuntimeManagedScopePolicyReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    blocked_refs = list(RUNTIME_MANAGED_SCOPE_POLICY_BLOCKED_AUTHORITY_REFS)
    pinned_sources = [
        RuntimeManagedScopePolicyPinSource(
            source_ref="managed-policy-source-ref:runtime:agents-md-baseline",
            source_kind=RuntimeManagedScopePolicySourceKind.repo_local_policy,
            display_label="Workspace standards baseline",
            precedence=1,
            checksum_ref="checksum-ref:managed-scope-policy:agents-md-baseline",
            safe_summary=(
                "Workspace standards pin runtime authority defaults for local review."
            ),
            blocked_authority_refs=blocked_refs,
        ),
        RuntimeManagedScopePolicyPinSource(
            source_ref="managed-policy-source-ref:runtime:hermes-adoption-pack",
            source_kind=RuntimeManagedScopePolicySourceKind.prompt_pack_policy,
            display_label="Hermes adoption prompt pack",
            precedence=2,
            checksum_ref="checksum-ref:managed-scope-policy:hermes-pack",
            safe_summary=(
                "Hermes adoption policy pins UAA-owned runtime delegation boundaries."
            ),
            blocked_authority_refs=blocked_refs,
        ),
        RuntimeManagedScopePolicyPinSource(
            source_ref="managed-policy-source-ref:runtime:sealed-default-profile",
            source_kind=RuntimeManagedScopePolicySourceKind.runtime_default,
            display_label="Sealed default runtime profile",
            precedence=3,
            checksum_ref="checksum-ref:managed-scope-policy:sealed-default",
            drift_status=RuntimeManagedScopeDriftStatus.warning,
            drift_warning_ref="drift-warning-ref:managed-scope-policy:sealed-default",
            safe_summary=(
                "Sealed default differs from requested runtime pilot scope; review stays local."
            ),
            blocked_authority_refs=blocked_refs,
        ),
    ]
    drift_warnings = [
        RuntimeManagedScopePolicyDriftWarning(
            warning_ref="drift-warning-ref:managed-scope-policy:sealed-default",
            source_ref="managed-policy-source-ref:runtime:sealed-default-profile",
            status=RuntimeManagedScopeDriftStatus.warning,
            severity="medium",
            expected_policy_ref="managed-policy-ref:runtime:local-operator-pilot",
            observed_policy_ref="managed-policy-ref:runtime:sealed-default",
            safe_summary=(
                "Requested pilot scope is visible as review posture; sealed default stays deny-by-default."
            ),
            blocked_authority_refs=blocked_refs,
            proof_refs=[RUNTIME_MANAGED_SCOPE_POLICY_PROOF_REF],
        )
    ]
    payload_for_hash: dict[str, object] = {
        "sources": [
            source.model_dump(mode="json", exclude={"checksum_ref"})
            for source in pinned_sources
        ],
        "drift": [warning.model_dump(mode="json") for warning in drift_warnings],
        "blocked": blocked_refs,
        "authority_state_decision_ref": authority_entry.decision.decision_ref,
        "authority_state_decision_outcome": _authority_value(
            authority_entry.decision.outcome
        ),
    }
    return RuntimeManagedScopePolicyReadModel(
        snapshot_hash_ref=_snapshot_hash_ref(payload_for_hash),
        authority_state_route_ref=RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_STATE_CLI_REF,
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
        pinned_sources=pinned_sources,
        drift_warnings=drift_warnings,
        pinned_source_count=len(pinned_sources),
        active_pinned_source_count=sum(1 for source in pinned_sources if source.active),
        drift_warning_count=len(drift_warnings),
        blocked_drift_warning_count=sum(
            1
            for warning in drift_warnings
            if warning.status == RuntimeManagedScopeDriftStatus.blocked.value
        ),
        blocked_authority_refs=blocked_refs,
        promotion_path_refs=[
            "promotion-path-ref:managed-scope:local-config-source",
            "promotion-path-ref:managed-scope:precedence-verification",
            "promotion-path-ref:managed-scope:redacted-protected-material-refs",
            "promotion-path-ref:managed-scope:rollback-proof",
            "promotion-path-ref:managed-scope:admin-operator-proof",
        ],
        proof_refs=[
            RUNTIME_MANAGED_SCOPE_POLICY_PROOF_REF,
            "proof-ref:managed-scope-policy:pinned-source-precedence",
            "proof-ref:managed-scope-policy:drift-warning-review",
        ],
        verifier_refs=[RUNTIME_MANAGED_SCOPE_POLICY_VERIFIER_REF],
        next_safe_action_refs=[
            "next-safe-action-ref:managed-scope:add-local-config-source",
            "next-safe-action-ref:managed-scope:verify-source-precedence",
            "next-safe-action-ref:managed-scope:add-rollback-proof",
        ],
    )


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry] | None,
) -> AuthorityDecisionCatalogEntry:
    catalog = authority_decision_catalog or build_authority_decision_catalog()
    for entry in catalog:
        if entry.lane_ref == RUNTIME_MANAGED_SCOPE_POLICY_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_MANAGED_SCOPE_AUTHORITY_MAPPING_MISSING")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
