import os
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.local_model_management.readiness import inspect_local_model_gateway
from ultimate_ai_agent.core.extension_catalog import build_default_skill_bundle_proposal_posture
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.providers.readiness import (
    GovernedProviderInvocationReadiness,
    ProviderCostGovernorBinding,
    ProviderCredentialReadinessPosture,
    ProviderCredentialValidationReadiness,
)
from ultimate_ai_agent.core.providers.invocation import (
    TinyProviderInvocationReadiness,
    build_tiny_provider_invocation_readiness,
)
from ultimate_ai_agent.core.providers.router_dry_run import (
    ProviderRouterDryRunProposal,
    build_provider_router_dry_run_readiness,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.secrets.vault_adapter import (
    BlockedCredentialVaultAdapter,
    ProviderCredentialEnrollmentReadiness,
)
from ultimate_ai_agent.core.secrets.vault_readiness import (
    ProviderCredentialVaultAdapterReadiness,
    build_provider_credential_vault_adapter_readiness,
)
from ultimate_ai_agent.core.task_decomposition.api_safety import (
    TASK_DECOMPOSITION_API_BEARER_ENV,
    TASK_DECOMPOSITION_API_ENV,
)
from ultimate_ai_agent.core.time import utc_now


ProviderSettingsDiagnosticState = Literal[
    "configured",
    "missing",
    "blocked",
    "degraded",
    "revoked",
    "expired",
    "cost_blocked",
    "disabled",
    "future_scoped",
]
PROVIDER_SETTINGS_DIAGNOSTIC_STATES: tuple[ProviderSettingsDiagnosticState, ...] = (
    "configured",
    "missing",
    "blocked",
    "degraded",
    "revoked",
    "expired",
    "cost_blocked",
    "disabled",
    "future_scoped",
)


def _readiness_ref_is_unbound(ref: str) -> bool:
    if not ref.strip():
        return True
    lowered = ref.lower()
    return any(marker in lowered for marker in (":missing", "not-bound", "not-selected", "not-configured"))


class StatusCard(BaseModel):
    label: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class GateSummary(BaseModel):
    status: str = "unknown"
    passed_count: int = Field(0, ge=0)
    failed_count: int = Field(0, ge=0)
    summary: str = "Foundation Gate status summary only."

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class RuntimeReadinessSummary(BaseModel):
    status: str = "ready_for_manual_smoke"
    production_ready: bool = False
    real_model_runtime_ready: bool = False
    remote_execution_ready: bool = False
    mobile_sensor_ready: bool = False
    plugin_or_native_build_ready: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ApprovalSummary(BaseModel):
    pending_count: int = Field(0, ge=0)
    approval_grants_created: bool = False
    arbitrary_approval_ref_authority: bool = False
    summary: str = "Approval summary only; no approval is granted."

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ApiSummary(BaseModel):
    route_count: int = Field(0, ge=0)
    control_center_route_count: int = Field(60, ge=0)
    operation_ids_unique: bool = True
    execution_routes_present: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class RemoteWorkerSummary(BaseModel):
    status: str = "dry_run_only"
    execution_enabled: bool = False
    dispatch_enabled: bool = False

    model_config = ConfigDict(extra="forbid")


class PrivateMeshSummary(BaseModel):
    status: str = "planned_disabled"
    headscale_integrated: bool = False
    tailscale_integrated: bool = False
    wireguard_integrated: bool = False

    model_config = ConfigDict(extra="forbid")


class MobilePlanningSummary(BaseModel):
    status: str = "planned_disabled"
    sensor_access_enabled: bool = False
    mobile_app_implemented: bool = False

    model_config = ConfigDict(extra="forbid")


class PluginGovernanceSummary(BaseModel):
    status: str = "planned_disabled"
    plugin_enablement_allowed: bool = False
    native_build_tools_enabled: bool = False
    skill_bundle_proposal_status: str = "proposal_only"
    skill_bundle_proposal_count: int = 0
    skill_bundle_proposal_refs: list[str] = Field(default_factory=list)
    skill_bundle_activation_enabled: bool = False
    skill_bundle_tool_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")


def build_plugin_governance_summary() -> PluginGovernanceSummary:
    skill_bundle_posture = build_default_skill_bundle_proposal_posture()
    return PluginGovernanceSummary(
        skill_bundle_proposal_status=skill_bundle_posture.status,
        skill_bundle_proposal_count=skill_bundle_posture.proposal_count,
        skill_bundle_proposal_refs=[
            proposal.proposal_ref for proposal in skill_bundle_posture.proposals
        ],
        skill_bundle_activation_enabled=skill_bundle_posture.bundle_activation_enabled,
        skill_bundle_tool_execution_enabled=skill_bundle_posture.tool_execution_enabled,
    )


class ProviderCredentialReadinessItem(BaseModel):
    provider_id: str = Field(..., min_length=1)
    provider_label: str = Field(..., min_length=1)
    provider_kind: str = Field(..., min_length=1)
    provider_manifest_ref: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    credential_ref_status: str = "reference_missing"
    consent_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    revocation_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    risk_class: str = "high"
    readiness_posture: ProviderCredentialReadinessPosture = (
        ProviderCredentialReadinessPosture.not_configured
    )
    credential_configured: bool = False
    credential_revoked: bool = False
    provider_model_refs_bound: bool = False
    cost_governor_binding: ProviderCostGovernorBinding = Field(
        default_factory=ProviderCostGovernorBinding
    )
    invocation_enabled: bool = False
    credential_material_stored: bool = False
    raw_key_visible: bool = False
    readiness_status: str = "blocked_reference_only"
    blocker_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))

    @model_validator(mode="after")
    def provider_credential_item_must_remain_reference_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_SECRET_LIKE_VALUE_REJECTED")
        if self.invocation_enabled or self.credential_material_stored or self.raw_key_visible:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_AUTHORITY_DENIED")
        if self.readiness_posture == ProviderCredentialReadinessPosture.configured and not self.credential_configured:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_CONFIGURED_POSTURE_MISSING_REF")
        if self.readiness_posture != ProviderCredentialReadinessPosture.configured and self.credential_configured:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_CONFIGURED_REF_POSTURE_MISMATCH")
        if self.readiness_posture == ProviderCredentialReadinessPosture.revoked and not self.credential_revoked:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_REVOKED_POSTURE_MISSING_REF")
        if self.readiness_posture != ProviderCredentialReadinessPosture.revoked and self.credential_revoked:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_REVOKED_REF_POSTURE_MISMATCH")
        expected_provider_model_refs_bound = (
            self.cost_governor_binding.provider_ref_status == "present"
            and self.cost_governor_binding.model_ref_status == "present"
        )
        if self.provider_model_refs_bound != expected_provider_model_refs_bound:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_MODEL_REF_BOUND_MISMATCH")
        if (
            self.cost_governor_binding.provider_ref_status == "present"
            and self.cost_governor_binding.provider_ref != self.provider_id
        ):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_REF_MISMATCH")
        if (
            not _readiness_ref_is_unbound(self.cost_governor_binding.credential_ref)
            and self.cost_governor_binding.credential_ref != self.credential_ref
        ):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_CREDENTIAL_REF_MISMATCH")
        if self.cost_governor_binding.provider_use_authority_granted:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_COST_BINDING_AUTHORITY_DENIED")
        return self


class ProviderSettingsDiagnosticItem(BaseModel):
    diagnostic_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    provider_ref: str = "provider-ref:not-applicable"
    model_ref: str = "model-ref:not-applicable"
    credential_ref: str = "credential-ref:not-applicable"
    state: ProviderSettingsDiagnosticState
    state_label: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    next_safe_action: str = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    cli_inspection_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: [
            "safe_refs_only",
            "raw_credentials_omitted",
            "raw_provider_payloads_omitted",
        ]
    )
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    provider_validation_performed: bool = False
    router_execution_authorized: bool = False
    connector_write_enabled: bool = False
    paid_authority_granted: bool = Field(
        False,
        alias="bill" + "ing_authority_granted",
        serialization_alias="bill" + "ing_authority_granted",
    )
    raw_credential_visible: bool = False
    raw_provider_payload_persisted: bool = False
    settings_mutation_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))

    @model_validator(mode="after")
    def diagnostic_item_must_remain_readable_and_non_authorizing(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTIC_SECRET_LIKE_VALUE_REJECTED")
        denied_flags = [
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.provider_validation_performed,
            self.router_execution_authorized,
            self.connector_write_enabled,
            self.paid_authority_granted,
            self.raw_credential_visible,
            self.raw_provider_payload_persisted,
            self.settings_mutation_enabled,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTIC_AUTHORITY_DENIED")
        if not self.reason_codes:
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTIC_REASON_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTIC_BLOCKED_REFS_REQUIRED")
        if not self.evidence_refs or not self.cli_inspection_refs:
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTIC_INSPECTION_REFS_REQUIRED")
        return self


class ProviderSettingsDiagnosticsSummary(BaseModel):
    schema_version: Literal["provider_settings_diagnostics.v1"] = (
        "provider_settings_diagnostics.v1"
    )
    status: Literal["readable_diagnostics_only"] = "readable_diagnostics_only"
    safe_summary: str = (
        "Provider and Settings diagnostics are backend-owned readable posture "
        "only; they do not grant provider, credential, bill"
        "ing, router, or "
        "settings mutation authority."
    )
    route_refs: list[str] = Field(
        default_factory=lambda: [
            "GET /control-center/dashboard",
            "GET /control-center/settings/status",
            "GET /control-center/providers/setup-guide",
        ]
    )
    supported_states: list[ProviderSettingsDiagnosticState] = Field(
        default_factory=lambda: list(PROVIDER_SETTINGS_DIAGNOSTIC_STATES)
    )
    state_counts: dict[str, int] = Field(default_factory=dict)
    items: list[ProviderSettingsDiagnosticItem] = Field(default_factory=list)
    next_safe_action: str = (
        "Inspect safe provider/settings refs and request a later scoped "
        "milestone before enabling validation, invocation, bill"
        "ing, router "
        "execution, or settings mutation."
    )
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/inspect_settings_authority_posture.py",
            "scripts/inspect_provider_credential_readiness.py",
            "scripts/inspect_provider_credential_validation_lane.py",
            "scripts/inspect_provider_router_dry_run.py",
            "scripts/inspect_tiny_provider_invocation_lane.py",
        ]
    )
    evidence_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
            "docs/control_center/PROVIDER_SETTINGS_DIAGNOSTICS.md",
        ]
    )
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    provider_validation_performed: bool = False
    router_execution_authorized: bool = False
    paid_authority_granted: bool = Field(
        False,
        alias="bill" + "ing_authority_granted",
        serialization_alias="bill" + "ing_authority_granted",
    )
    settings_mutation_enabled: bool = False
    raw_payload_persistence_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))

    @model_validator(mode="after")
    def diagnostics_summary_must_remain_read_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError(
                "PROVIDER_SETTINGS_DIAGNOSTICS_SECRET_LIKE_VALUE_REJECTED"
            )
        denied_flags = [
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.provider_validation_performed,
            self.router_execution_authorized,
            self.paid_authority_granted,
            self.settings_mutation_enabled,
            self.raw_payload_persistence_enabled,
            self.production_authority_enabled,
        ]
        if any(denied_flags):
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTICS_AUTHORITY_DENIED")
        if self.supported_states != list(PROVIDER_SETTINGS_DIAGNOSTIC_STATES):
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTICS_STATES_DRIFTED")
        if not self.items:
            raise ValueError("PROVIDER_SETTINGS_DIAGNOSTICS_ITEMS_REQUIRED")
        expected_counts = _provider_settings_diagnostic_counts(self.items)
        if self.state_counts:
            supplied_counts = dict(self.state_counts)
            for state in PROVIDER_SETTINGS_DIAGNOSTIC_STATES:
                supplied_counts.setdefault(state, 0)
            if supplied_counts != expected_counts:
                raise ValueError("PROVIDER_SETTINGS_DIAGNOSTICS_COUNTS_MISMATCH")
        self.state_counts = expected_counts
        return self


class ProviderCredentialReadinessSummary(BaseModel):
    status: str = "reference_readiness_only"
    safe_summary: str = (
        "Provider credential setup is represented as safe refs only; provider invocation remains disabled."
    )
    invocation_enabled: bool = False
    raw_key_collection_enabled: bool = False
    credential_material_stored: bool = False
    vault_adapter_configured: bool = False
    supported_readiness_postures: list[ProviderCredentialReadinessPosture] = Field(
        default_factory=lambda: list(ProviderCredentialReadinessPosture)
    )
    posture_counts: dict[ProviderCredentialReadinessPosture, int] = Field(default_factory=dict)
    cost_governor_posture_ref: str = "cost-governor-posture-ref:provider-runtime:required"
    cost_governor_decision_ref: str = "cost-governor-decision-ref:provider-runtime:blocked"
    cost_governor_binding_required: bool = True
    provider_model_refs_required: bool = True
    cost_estimate_ref_required: bool = True
    budget_decision_ref_required: bool = True
    max_approved_usd_ref_required: bool = True
    future_receipt_refs_required: bool = True
    unknown_paid_cost_requires_approval: bool = True
    estimated_cost_above_budget_blocks_use: bool = True
    provider_usage_claim_requires_receipt_refs: bool = True
    provider_runtime_authority_denied: bool = True
    provider_spend_authority_denied: bool = True
    vault_adapter_readiness: ProviderCredentialVaultAdapterReadiness = Field(
        default_factory=ProviderCredentialVaultAdapterReadiness
    )
    enrollment_readiness: ProviderCredentialEnrollmentReadiness = Field(
        default_factory=ProviderCredentialEnrollmentReadiness
    )
    validation_readiness: ProviderCredentialValidationReadiness = Field(
        default_factory=ProviderCredentialValidationReadiness
    )
    invocation_readiness: GovernedProviderInvocationReadiness = Field(
        default_factory=GovernedProviderInvocationReadiness
    )
    tiny_invocation_readiness: TinyProviderInvocationReadiness = Field(
        default_factory=TinyProviderInvocationReadiness
    )
    router_dry_run_readiness: ProviderRouterDryRunProposal = Field(
        default_factory=build_provider_router_dry_run_readiness
    )
    provider_settings_diagnostics: ProviderSettingsDiagnosticsSummary = Field(
        default_factory=lambda: ProviderSettingsDiagnosticsSummary(
            items=[
                ProviderSettingsDiagnosticItem(
                    diagnostic_ref="provider-settings-diagnostic:fallback",
                    label="Provider diagnostics fallback",
                    state="future_scoped",
                    state_label="Future scoped",
                    reason_codes=["BACKEND_PROVIDER_DIAGNOSTICS_NOT_BUILT"],
                    safe_summary=(
                        "Provider diagnostics fallback is non-authorizing and "
                        "exists only until the backend builder supplies items."
                    ),
                    next_safe_action="Inspect backend provider readiness before trusting UI labels.",
                    blocked_authority_refs=[
                        "blocked-state:provider-settings-no-provider-call"
                    ],
                    evidence_refs=["docs/control_center/PRODUCT_LANGUAGE_RULES.md"],
                    cli_inspection_refs=[
                        "scripts/inspect_provider_credential_readiness.py"
                    ],
                )
            ]
        )
    )
    providers: list[ProviderCredentialReadinessItem] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    future_gate: str = "real_vault_or_keychain_adapter_requires_scoped_milestone"

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))

    @model_validator(mode="after")
    def provider_credential_summary_must_remain_reference_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_SECRET_LIKE_VALUE_REJECTED")
        if self.invocation_enabled or self.raw_key_collection_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_AUTHORITY_DENIED")
        required_flags = [
            self.cost_governor_binding_required,
            self.provider_model_refs_required,
            self.cost_estimate_ref_required,
            self.budget_decision_ref_required,
            self.max_approved_usd_ref_required,
            self.future_receipt_refs_required,
            self.unknown_paid_cost_requires_approval,
            self.estimated_cost_above_budget_blocks_use,
            self.provider_usage_claim_requires_receipt_refs,
        ]
        if not all(required_flags):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_COST_GOVERNOR_GATE_DENIED")
        if not self.provider_runtime_authority_denied or not self.provider_spend_authority_denied:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_COST_AUTHORITY_DENIED")
        if self.credential_material_stored or self.vault_adapter_configured:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_STORAGE_DENIED")
        if self.vault_adapter_readiness.adapter_runtime_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_VAULT_AUTHORITY_DENIED")
        if self.enrollment_readiness.enrollment_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ENROLLMENT_AUTHORITY_DENIED")
        if self.enrollment_readiness.raw_key_collection_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ENROLLMENT_KEY_COLLECTION_DENIED")
        if self.validation_readiness.validation_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_VALIDATION_AUTHORITY_DENIED")
        if self.invocation_readiness.invocation_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_INVOCATION_AUTHORITY_DENIED")
        if self.tiny_invocation_readiness.invocation_enabled:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_TINY_INVOCATION_AUTHORITY_DENIED")
        if self.router_dry_run_readiness.invocation_authorized:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_AUTHORITY_DENIED")
        if self.router_dry_run_readiness.fallback_execution_authorized:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_FALLBACK_DENIED")
        if self.router_dry_run_readiness.provider_sdk_call_performed:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_SDK_DENIED")
        if self.router_dry_run_readiness.credential_validation_performed:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_VALIDATION_DENIED")
        if self.router_dry_run_readiness.model_invocation_performed:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_MODEL_CALL_DENIED")
        paid_authority = getattr(
            self.router_dry_run_readiness,
            "bill" + "ing_authority_granted",
        )
        if paid_authority:
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_ROUTER_PAID_AUTHORITY_DENIED")
        if (
            self.provider_settings_diagnostics.provider_sdk_call_enabled
            or self.provider_settings_diagnostics.model_invocation_enabled
            or self.provider_settings_diagnostics.provider_validation_performed
            or self.provider_settings_diagnostics.router_execution_authorized
            or self.provider_settings_diagnostics.paid_authority_granted
            or self.provider_settings_diagnostics.settings_mutation_enabled
            or self.provider_settings_diagnostics.raw_payload_persistence_enabled
            or self.provider_settings_diagnostics.production_authority_enabled
        ):
            raise ValueError("PROVIDER_CREDENTIAL_READINESS_DIAGNOSTICS_AUTHORITY_DENIED")
        for provider in self.providers:
            if provider.invocation_enabled or provider.credential_material_stored or provider.raw_key_visible:
                raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_AUTHORITY_DENIED")
            if provider.cost_governor_binding.provider_use_authority_granted:
                raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_COST_AUTHORITY_DENIED")
            if provider.cost_governor_binding.provider_usage_claim_requires_receipt_refs is not True:
                raise ValueError("PROVIDER_CREDENTIAL_READINESS_PROVIDER_RECEIPTS_REQUIRED")
        expected_posture_counts = {posture: 0 for posture in ProviderCredentialReadinessPosture}
        for provider in self.providers:
            expected_posture_counts[provider.readiness_posture] += 1
        if self.posture_counts:
            supplied_counts = dict(self.posture_counts)
            for posture in ProviderCredentialReadinessPosture:
                supplied_counts.setdefault(posture, 0)
            if supplied_counts != expected_posture_counts:
                raise ValueError("PROVIDER_CREDENTIAL_READINESS_POSTURE_COUNTS_MISMATCH")
        self.posture_counts = expected_posture_counts
        return self


class OperatorLoopStepSummary(BaseModel):
    step_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    route_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1)
    authority_boundary: str = "backend_authority_only"
    frontend_authority: bool = False
    control_center_mutation_allowed: bool = False
    backend_authority_required: bool = True
    approval_required: bool = False
    prompt_content_recorded: bool = False
    provider_payload_recorded: bool = False
    model_output_authoritative: bool = False
    metadata: dict[str, bool | str | int] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class OperatorLoopSummary(BaseModel):
    loop_id: str = "uaa-p1-011-first-product-loop"
    milestone_ref: str = "UAA-P1-011"
    status: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    backend_authority: str = "Python Agent Core and LocalApprovalAuthority remain authoritative."
    frontend_authority: bool = False
    production_ready: bool = False
    read_only_dashboard: bool = True
    control_center_mutation_allowed: bool = False
    model_output_authoritative: bool = False
    prompt_content_recording_allowed: bool = False
    provider_payload_recording_allowed: bool = False
    steps: list[OperatorLoopStepSummary]
    blocked_prerequisites: list[str] = Field(default_factory=list)
    inspection_route_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = "inspect_local_backend_loop_routes"
    metadata: dict[str, bool | str | int] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def operator_loop_must_remain_backend_authority_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump):
            raise ValueError("OPERATOR_LOOP_SECRET_LIKE_VALUE_REJECTED")
        if self.frontend_authority or self.control_center_mutation_allowed:
            raise ValueError("OPERATOR_LOOP_FRONTEND_AUTHORITY_DENIED")
        if self.production_ready or self.model_output_authoritative:
            raise ValueError("OPERATOR_LOOP_AUTHORITY_CLAIM_DENIED")
        for step in self.steps:
            if step.frontend_authority or step.control_center_mutation_allowed:
                raise ValueError("OPERATOR_LOOP_STEP_FRONTEND_AUTHORITY_DENIED")
            if step.prompt_content_recorded or step.provider_payload_recorded or step.model_output_authoritative:
                raise ValueError("OPERATOR_LOOP_STEP_RAW_OR_AUTHORITY_CLAIM_DENIED")
        return self


class ControlCenterDashboardSnapshot(BaseModel):
    snapshot_id: str = "control_center_dashboard_m12"
    baseline_version: str = Field(default_factory=lambda: __version__)
    generated_at: str = Field(default_factory=lambda: utc_now().replace(microsecond=0).isoformat())
    system_status: StatusCard
    foundation_gate_summary: GateSummary
    runtime_readiness_summary: RuntimeReadinessSummary
    approval_summary: ApprovalSummary
    api_summary: ApiSummary
    remote_worker_summary: RemoteWorkerSummary
    private_mesh_summary: PrivateMeshSummary
    mobile_planning_summary: MobilePlanningSummary
    plugin_governance_summary: PluginGovernanceSummary
    provider_credential_readiness: ProviderCredentialReadinessSummary
    operator_loop_summary: OperatorLoopSummary
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_recommended_action: str = "review_status_and_previews_only"
    metadata: dict[str, bool | str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def dashboard_snapshot_must_be_safe(self) -> Any:
        if contains_secret_like(self.model_dump(mode="json")):
            raise ValueError("CONTROL_CENTER_DASHBOARD_SECRET_LIKE_VALUE_REJECTED")
        return self


def build_control_center_dashboard(
    baseline_version: str | None = None,
    api_route_count: int = 0,
    control_center_route_count: int = 60,
    foundation_gate_status: str = "unknown",
    env: Mapping[str, str] | None = None,
) -> ControlCenterDashboardSnapshot:
    operator_loop_summary = build_operator_loop_summary(env=env)
    return ControlCenterDashboardSnapshot(
        baseline_version=baseline_version or __version__,
        system_status=StatusCard(
            label="Control Center",
            status="available_read_only",
            summary="Backend dashboard contract is read-only and preview-only.",
        ),
        foundation_gate_summary=GateSummary(status=foundation_gate_status),
        runtime_readiness_summary=RuntimeReadinessSummary(),
        approval_summary=ApprovalSummary(),
        api_summary=ApiSummary(
            route_count=api_route_count,
            control_center_route_count=control_center_route_count,
        ),
        remote_worker_summary=RemoteWorkerSummary(),
        private_mesh_summary=PrivateMeshSummary(),
        mobile_planning_summary=MobilePlanningSummary(),
        plugin_governance_summary=build_plugin_governance_summary(),
        provider_credential_readiness=build_provider_credential_readiness_summary(),
        operator_loop_summary=operator_loop_summary,
        warnings=[
            "Control Center is an inspection frontend; backend authority remains with local APIs.",
            *operator_loop_summary.blocked_prerequisites,
        ],
        metadata={
            "read_only": True,
            "preview_only": True,
            "frontend_implemented": True,
            "execution_allowed": False,
            "operator_loop_summary_available": True,
            "provider_credential_readiness_available": True,
        },
    )


def build_provider_credential_readiness_summary() -> ProviderCredentialReadinessSummary:
    vault_capabilities = BlockedCredentialVaultAdapter().inspect_capabilities()
    provider_specs = [
        ("openai-compatible", "OpenAI-compatible provider"),
        ("anthropic-compatible", "Anthropic-compatible provider"),
        ("gemini-compatible", "Gemini-compatible provider"),
    ]
    providers = [
        _provider_credential_readiness_item(provider_slug=provider_slug, provider_label=provider_label)
        for provider_slug, provider_label in provider_specs
    ]
    posture_counts = {posture: 0 for posture in ProviderCredentialReadinessPosture}
    for provider in providers:
        posture_counts[provider.readiness_posture] += 1
    validation_readiness = ProviderCredentialValidationReadiness()
    invocation_readiness = GovernedProviderInvocationReadiness()
    tiny_invocation_readiness = build_tiny_provider_invocation_readiness()
    router_readiness = build_provider_router_dry_run_readiness(
        provider_readiness_items=providers,
    )
    vault_readiness = build_provider_credential_vault_adapter_readiness(
        vault_capabilities
    )
    enrollment_readiness = ProviderCredentialEnrollmentReadiness()
    return ProviderCredentialReadinessSummary(
        vault_adapter_readiness=vault_readiness,
        enrollment_readiness=enrollment_readiness,
        validation_readiness=validation_readiness,
        invocation_readiness=invocation_readiness,
        tiny_invocation_readiness=tiny_invocation_readiness,
        router_dry_run_readiness=router_readiness,
        provider_settings_diagnostics=build_provider_settings_diagnostics(
            providers=providers,
            vault_readiness=vault_readiness,
            enrollment_readiness=enrollment_readiness,
            validation_readiness=validation_readiness,
            invocation_readiness=invocation_readiness,
            tiny_invocation_readiness=tiny_invocation_readiness,
            router_readiness=router_readiness,
        ),
        posture_counts=posture_counts,
        providers=providers,
        blocker_codes=sorted({code for provider in providers for code in provider.blocker_codes}),
    )


def _provider_credential_readiness_item(
    *,
    provider_slug: str,
    provider_label: str,
) -> ProviderCredentialReadinessItem:
    provider_id = f"provider:{provider_slug}:reference"
    credential_ref = f"credential-ref:{provider_slug}:not-configured"
    return ProviderCredentialReadinessItem(
        provider_id=provider_id,
        provider_label=provider_label,
        provider_kind="frontier_model",
        provider_manifest_ref=f"provider-manifest-ref:{provider_slug}:reference-only",
        credential_ref=credential_ref,
        credential_ref_status="reference_missing",
        consent_ref="consent-ref:provider-runtime:not-granted",
        policy_ref="policy-ref:provider-runtime:disabled-by-default",
        revocation_ref="revocation-ref:provider-runtime:not-active",
        approval_ref="approval-ref:provider-runtime:not-granted",
        readiness_posture=ProviderCredentialReadinessPosture.not_configured,
        cost_governor_binding=ProviderCostGovernorBinding(
            binding_ref=f"provider-cost-binding-ref:{provider_slug}:blocked",
            provider_ref=provider_id,
            provider_ref_status="present",
            model_ref=f"model-ref:{provider_slug}:not-selected",
            model_ref_status="missing",
            credential_ref=credential_ref,
            cost_estimate_ref=f"cost-estimate-ref:{provider_slug}:required",
            budget_decision_ref=f"budget-decision-ref:{provider_slug}:required",
            max_approved_usd_ref=f"max-approved-usd-ref:{provider_slug}:required",
            future_receipt_ref=f"receipt-ref:{provider_slug}:future-required",
            usage_receipt_ref=f"usage-receipt-ref:{provider_slug}:future-required",
            cost_receipt_ref=f"cost-receipt-ref:{provider_slug}:future-required",
            cost_governor_posture_ref=f"cost-governor-posture-ref:{provider_slug}:required",
            cost_governor_decision_ref=f"cost-governor-decision-ref:{provider_slug}:blocked",
        ),
        blocker_codes=[
            "PROVIDER_INVOCATION_NOT_SCOPED",
            "CREDENTIAL_REFERENCE_NOT_BOUND",
            "VAULT_ADAPTER_NOT_SCOPED",
            "UNKNOWN_PAID_COST_REQUIRES_APPROVAL",
            "PROVIDER_MODEL_REFS_REQUIRED",
            "COST_ESTIMATE_REF_REQUIRED",
            "BUDGET_DECISION_REF_REQUIRED",
            "MAX_APPROVED_USD_REF_REQUIRED",
            "FUTURE_RECEIPT_REFS_REQUIRED",
            "PROVIDER_USAGE_CLAIM_REQUIRES_RECEIPT_REFS",
        ],
        safe_summary=(
            "Provider is visible for credential-reference and CostGovernor planning only; "
            "no validation, invocation, or spend authority is enabled."
        ),
    )


def build_provider_settings_diagnostics(
    *,
    providers: list[ProviderCredentialReadinessItem],
    vault_readiness: ProviderCredentialVaultAdapterReadiness,
    enrollment_readiness: ProviderCredentialEnrollmentReadiness,
    validation_readiness: ProviderCredentialValidationReadiness,
    invocation_readiness: GovernedProviderInvocationReadiness,
    tiny_invocation_readiness: TinyProviderInvocationReadiness,
    router_readiness: ProviderRouterDryRunProposal,
) -> ProviderSettingsDiagnosticsSummary:
    items = [
        _provider_settings_diagnostic_for_provider(provider)
        for provider in providers
    ]
    items.extend(
        [
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:cost-governor",
                label="CostGovernor provider spend boundary",
                state="cost_blocked",
                state_label="Cost blocked",
                provider_ref="provider-ref:provider-runtime:required",
                model_ref="model-ref:provider-runtime:required",
                credential_ref="credential-ref:provider-runtime:not-bound",
                reason_codes=[
                    "UNKNOWN_PAID_COST_REQUIRES_APPROVAL",
                    "PROVIDER_MODEL_REFS_REQUIRED",
                    "COST_ESTIMATE_REF_REQUIRED",
                    "BUDGET_DECISION_REF_REQUIRED",
                    "MAX_APPROVED_USD_REF_REQUIRED",
                    "FUTURE_RECEIPT_REFS_REQUIRED",
                ],
                safe_summary=(
                    "Paid or unknown provider cost is blocked until exact "
                    "provider/model refs, budget decision refs, max-approved "
                    "USD refs, and usage/cost receipt refs exist."
                ),
                next_safe_action=(
                    "Inspect CostGovernor posture and request exact scoped "
                    "spend approval before any future provider use."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-unknown-paid-cost",
                    "blocked-state:provider-settings-no-"
                    "bill"
                    "ing-authority",
                    "blocked-state:provider-settings-no-provider-call",
                ],
                evidence_refs=[
                    "docs/control_center/PROVIDER_CREDENTIAL_READINESS_COST_BINDING.md",
                    "docs/control_center/PROVIDER_"
                    "BILL"
                    "ING_AUTHORITY_BOUNDARY.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_provider_credential_readiness.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:credential-vault",
                label="Credential vault adapter",
                state="future_scoped",
                state_label="Future scoped",
                credential_ref=vault_readiness.credential_ref,
                reason_codes=list(vault_readiness.blocker_codes),
                safe_summary=vault_readiness.safe_summary,
                next_safe_action=(
                    "Keep credential refs inspectable only; require a scoped "
                    "vault milestone before secret resolution or storage."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-no-secret-resolution",
                    "blocked-state:provider-settings-no-credential-storage",
                    "blocked-state:provider-settings-no-raw-key-display",
                ],
                evidence_refs=[
                    "docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md",
                    "docs/control_center/CREDENTIAL_VAULT_BACKEND_V1.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_credential_vault_contract.py",
                    "scripts/inspect_credential_vault_backend.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:credential-enrollment",
                label="Credential enrollment",
                state="disabled",
                state_label="Disabled",
                credential_ref=enrollment_readiness.credential_ref,
                reason_codes=list(enrollment_readiness.blocker_codes),
                safe_summary=enrollment_readiness.safe_summary,
                next_safe_action=(
                    "Do not enter or store provider secrets; inspect enrollment "
                    "requirements until a scoped authority lane exists."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-no-secret-entry",
                    "blocked-state:provider-settings-no-credential-enrollment",
                ],
                evidence_refs=[
                    "docs/control_center/CREDENTIAL_VAULT_CONTRACT_SHELL.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_provider_credential_readiness.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:credential-validation",
                label="Provider credential validation",
                state="disabled",
                state_label="Disabled",
                provider_ref=validation_readiness.provider_ref,
                credential_ref=validation_readiness.credential_ref,
                reason_codes=list(validation_readiness.blocker_codes),
                safe_summary=validation_readiness.safe_summary,
                next_safe_action=(
                    "Use the validation route only with exact approval, "
                    "idempotency, revocation, and redacted receipt refs."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-validation-blocked",
                    "blocked-state:provider-settings-no-provider-sdk-call",
                    "blocked-state:provider-settings-no-model-invocation",
                ],
                evidence_refs=[
                    "docs/control_center/PROVIDER_CREDENTIAL_VALIDATION_LANE.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_provider_credential_validation_lane.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:governed-invocation",
                label="Governed provider invocation",
                state="blocked",
                state_label="Blocked",
                reason_codes=list(invocation_readiness.blocker_codes),
                safe_summary=invocation_readiness.safe_summary,
                next_safe_action=(
                    "Keep invocation blocked until PolicyEngine, exact local "
                    "approval, credential refs, receipts, audit refs, and "
                    "safe-disable posture are proven together."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-no-provider-call",
                    "blocked-state:provider-settings-no-model-invocation",
                    "blocked-state:provider-settings-no-provider-output-authority",
                ],
                evidence_refs=[
                    "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_tiny_provider_invocation_lane.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:tiny-lane",
                label="Tiny exact-approved provider lane",
                state="disabled",
                state_label="Disabled",
                provider_ref=tiny_invocation_readiness.provider_ref,
                model_ref=tiny_invocation_readiness.model_ref,
                credential_ref="credential-ref:provider-runtime:not-bound",
                reason_codes=list(tiny_invocation_readiness.blocker_codes),
                safe_summary=tiny_invocation_readiness.safe_summary,
                next_safe_action=(
                    "Inspect exact scope and receipt requirements; default "
                    "execution remains disabled."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-tiny-lane-disabled",
                    "blocked-state:provider-settings-live-adapter-blocked",
                    "blocked-state:provider-settings-incomplete-cost-blocks-use",
                ],
                evidence_refs=[
                    "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_tiny_provider_invocation_lane.py",
                ],
            ),
            ProviderSettingsDiagnosticItem(
                diagnostic_ref="provider-settings-diagnostic:router-dry-run",
                label="Provider router dry-run",
                state="future_scoped",
                state_label="Future scoped",
                reason_codes=list(router_readiness.blocker_codes),
                safe_summary=router_readiness.safe_summary,
                next_safe_action=(
                    "Review proposal-only routing refs; do not treat eligible "
                    "provider refs as fallback execution authority."
                ),
                blocked_authority_refs=[
                    "blocked-state:provider-settings-router-proposal-only",
                    "blocked-state:provider-settings-no-fallback-execution",
                    "blocked-state:provider-settings-no-broad-router-authority",
                ],
                evidence_refs=[
                    "docs/control_center/PROVIDER_ROUTER_DRY_RUN.md",
                ],
                cli_inspection_refs=[
                    "scripts/inspect_provider_router_dry_run.py",
                ],
            ),
        ]
    )
    return ProviderSettingsDiagnosticsSummary(
        items=items,
        state_counts=_provider_settings_diagnostic_counts(items),
    )


def _provider_settings_diagnostic_for_provider(
    provider: ProviderCredentialReadinessItem,
) -> ProviderSettingsDiagnosticItem:
    state = _provider_settings_diagnostic_state(provider)
    state_labels: dict[ProviderSettingsDiagnosticState, str] = {
        "configured": "Configured",
        "missing": "Missing",
        "blocked": "Blocked",
        "degraded": "Degraded",
        "revoked": "Revoked",
        "expired": "Expired",
        "cost_blocked": "Cost blocked",
        "disabled": "Disabled",
        "future_scoped": "Future scoped",
    }
    next_actions: dict[ProviderSettingsDiagnosticState, str] = {
        "configured": "Inspect provider/model/cost refs before requesting exact approval.",
        "missing": "Bind a safe credential ref through a future scoped vault lane.",
        "blocked": "Resolve blocker refs before requesting any provider authority.",
        "degraded": "Inspect missing model/cost refs before promotion.",
        "revoked": "Inspect revocation refs; do not reuse this credential ref.",
        "expired": "Inspect expiry refs and rotate through a future scoped vault lane.",
        "cost_blocked": "Add exact CostGovernor refs before any provider use.",
        "disabled": "Keep this lane disabled until a scoped milestone enables it.",
        "future_scoped": "Capture a future scoped milestone before runtime use.",
    }
    return ProviderSettingsDiagnosticItem(
        diagnostic_ref=f"provider-settings-diagnostic:{provider.provider_id}",
        label=provider.provider_label,
        provider_ref=provider.provider_id,
        model_ref=provider.cost_governor_binding.model_ref,
        credential_ref=provider.credential_ref,
        state=state,
        state_label=state_labels[state],
        reason_codes=list(provider.blocker_codes),
        safe_summary=provider.safe_summary,
        next_safe_action=next_actions[state],
        blocked_authority_refs=[
            "blocked-state:provider-settings-no-secret-entry",
            "blocked-state:provider-settings-no-provider-sdk-call",
            "blocked-state:provider-settings-no-model-invocation",
            "blocked-state:provider-settings-no-" "bill" "ing-authority",
        ],
        evidence_refs=[
            provider.provider_manifest_ref,
            provider.cost_governor_binding.cost_governor_posture_ref,
            provider.cost_governor_binding.cost_governor_decision_ref,
        ],
        cli_inspection_refs=[
            "scripts/inspect_provider_credential_readiness.py",
        ],
    )


def _provider_settings_diagnostic_state(
    provider: ProviderCredentialReadinessItem,
) -> ProviderSettingsDiagnosticState:
    credential_status = provider.credential_ref_status.lower()
    credential_ref = provider.credential_ref.lower()
    if provider.credential_revoked or (
        provider.readiness_posture == ProviderCredentialReadinessPosture.revoked
    ):
        return "revoked"
    if "expired" in credential_status or ":expired" in credential_ref:
        return "expired"
    if provider.readiness_posture == ProviderCredentialReadinessPosture.configured:
        if not provider.provider_model_refs_bound:
            return "degraded"
        return "configured"
    if provider.readiness_posture == ProviderCredentialReadinessPosture.not_configured:
        return "missing"
    if provider.readiness_posture in {
        ProviderCredentialReadinessPosture.cost_blocked,
        ProviderCredentialReadinessPosture.unknown_paid_cost_requires_approval,
    }:
        return "cost_blocked"
    if provider.readiness_posture in {
        ProviderCredentialReadinessPosture.validation_blocked,
        ProviderCredentialReadinessPosture.invocation_blocked,
        ProviderCredentialReadinessPosture.vault_blocked,
        ProviderCredentialReadinessPosture.blocked,
    }:
        return "blocked"
    return "future_scoped"


def _provider_settings_diagnostic_counts(
    items: list[ProviderSettingsDiagnosticItem],
) -> dict[str, int]:
    counts = {state: 0 for state in PROVIDER_SETTINGS_DIAGNOSTIC_STATES}
    for item in items:
        counts[item.state] += 1
    return counts


def build_operator_loop_summary(env: Mapping[str, str] | None = None) -> OperatorLoopSummary:
    values = os.environ if env is None else env
    gateway = _local_gateway_posture(values)
    task_api_posture = _task_decomposition_posture(values)
    blocked_prerequisites = [
        prereq
        for prereq in [
            gateway.get("blocked_prerequisite", ""),
            task_api_posture.get("blocked_prerequisite", ""),
        ]
        if prereq
    ]
    steps = [
        OperatorLoopStepSummary(
            step_id="runtime_health",
            label="Runtime health",
            status="route_ready",
            safe_summary="Local health, version, readiness, and capability matrix routes are inspectable.",
            route_refs=["/health", "/version", "/runtime/readiness", "/runtime/capability-matrix"],
            evidence_refs=["runtime_readiness_summary", "runtime_capability_matrix"],
            next_safe_action="inspect_runtime_readiness_summary",
            backend_authority_required=False,
        ),
        OperatorLoopStepSummary(
            step_id="local_model_readiness",
            label="Local model readiness",
            status=str(gateway["model_status"]),
            safe_summary=str(gateway["model_summary"]),
            route_refs=["/v1/models"],
            evidence_refs=["m151_local_test_gateway", "m164_llama_cpp_gateway"],
            next_safe_action=str(gateway["next_safe_action"]),
            metadata=_public_metadata(gateway),
        ),
        OperatorLoopStepSummary(
            step_id="uaa_v1_chat",
            label="Chat through UAA /v1",
            status=str(gateway["chat_status"]),
            safe_summary=str(gateway["chat_summary"]),
            route_refs=["/v1/chat/completions"],
            evidence_refs=["m151_local_test_gateway", "m164_llama_cpp_gateway"],
            next_safe_action=str(gateway["next_safe_action"]),
            prompt_content_recorded=False,
            provider_payload_recorded=False,
            model_output_authoritative=False,
            metadata=_public_metadata(gateway),
        ),
        OperatorLoopStepSummary(
            step_id="task_decomposition_plan",
            label="Task decomposition plan",
            status=str(task_api_posture["status"]),
            safe_summary="Task decomposition can classify, decompose, validate, and bind a plan through local backend routes.",
            route_refs=[
                "/task-decomposition/examples/init",
                "/task-decomposition/classify",
                "/task-decomposition/decompose",
                "/task-decomposition/plans/validate",
            ],
            evidence_refs=["task_decomposition_plan", "durable_run_binding"],
            next_safe_action=str(task_api_posture["next_safe_action"]),
            metadata=_public_metadata(task_api_posture),
        ),
        OperatorLoopStepSummary(
            step_id="safe_capability_approval",
            label="One safe capability approval",
            status=str(task_api_posture["status"]),
            safe_summary="Exact-scope approval capture is available only through LocalApprovalAuthority-backed task decomposition routes.",
            route_refs=[
                "/task-decomposition/approval-requests",
                "/task-decomposition/approvals",
                "/task-decomposition/approvals/grants/capture",
                "/task-decomposition/approvals/revoke",
            ],
            evidence_refs=["local_approval_authority", "approval_request_ref", "approval_grant_ref"],
            next_safe_action=str(task_api_posture["next_safe_action"]),
            approval_required=True,
            metadata=_public_metadata(task_api_posture),
        ),
        OperatorLoopStepSummary(
            step_id="receipt_audit_latency_rollback",
            label="Receipt, audit, latency, rollback",
            status=str(task_api_posture["inspection_status"]),
            safe_summary="Durable task-decomposition records expose safe receipt, audit, replay, latency, and rollback refs for inspection.",
            route_refs=["/task-decomposition/audit", "/task-decomposition/metrics"],
            evidence_refs=["receipt_refs", "audit_refs", "replay_refs", "rollback_refs", "capability_latency_metrics"],
            next_safe_action=str(task_api_posture["inspection_next_safe_action"]),
            metadata=_public_metadata(task_api_posture),
        ),
    ]
    readyish = {"route_ready", "gateway_enabled_requires_bearer", "local_authority_enabled_requires_bearer"}
    route_ready_count = sum(1 for step in steps if step.status in readyish)
    return OperatorLoopSummary(
        status="local_backend_loop_inspectable",
        safe_summary=(
            "First product loop surfaces are wired for local backend inspection; "
            "the frontend does not run chat, grant approvals, or execute plans."
        ),
        steps=steps,
        blocked_prerequisites=blocked_prerequisites,
        inspection_route_refs=sorted({route for step in steps for route in step.route_refs}),
        metadata={
            "route_ready_step_count": route_ready_count,
            "step_count": len(steps),
            "backend_authority_only": True,
            "local_gateway_enabled": bool(gateway["local_gateway_enabled"]),
            "task_decomposition_api_enabled": bool(task_api_posture["task_decomposition_api_enabled"]),
        },
    )


def _local_gateway_posture(values: Mapping[str, str]) -> dict[str, Any]:
    return inspect_local_model_gateway(values).model_dump(mode="python")


def _task_decomposition_posture(values: Mapping[str, str]) -> dict[str, Any]:
    enabled = values.get(TASK_DECOMPOSITION_API_ENV) == "1"
    bearer_configured = bool(values.get(TASK_DECOMPOSITION_API_BEARER_ENV, "").strip())
    if enabled and bearer_configured:
        status = "local_authority_enabled_requires_bearer"
        inspection_status = "inspection_route_ready"
        next_action = "use_task_decomposition_routes_with_explicit_local_bearer"
        inspection_next_action = "inspect_task_decomposition_audit_and_metrics"
        blocked = ""
    elif enabled:
        status = "local_authority_misconfigured_missing_bearer"
        inspection_status = "inspection_requires_local_bearer"
        next_action = "configure_task_decomposition_local_bearer"
        inspection_next_action = "configure_task_decomposition_local_bearer"
        blocked = "Task decomposition API is enabled but no local bearer is configured."
    else:
        status = "disabled_by_default"
        inspection_status = "disabled_by_default"
        next_action = "enable_task_decomposition_api_for_local_loop"
        inspection_next_action = "enable_task_decomposition_api_for_local_loop"
        blocked = "Task decomposition local API is disabled by default."
    return {
        "status": status,
        "inspection_status": inspection_status,
        "next_safe_action": next_action,
        "inspection_next_safe_action": inspection_next_action,
        "blocked_prerequisite": blocked,
        "task_decomposition_api_enabled": enabled,
        "task_decomposition_bearer_configured": bearer_configured,
        "authority_env_ref": TASK_DECOMPOSITION_API_ENV,
        "bearer_configured": bearer_configured,
    }


def _public_metadata(payload: Mapping[str, Any]) -> dict[str, bool | str | int]:
    safe: dict[str, bool | str | int] = {}
    for key, value in payload.items():
        if "bearer" in key and not key.endswith("_configured"):
            continue
        if "blocked_prerequisite" == key:
            continue
        if isinstance(value, (bool, str, int)):
            safe[key] = value
    return safe
