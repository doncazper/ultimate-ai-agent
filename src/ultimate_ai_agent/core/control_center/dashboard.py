import os
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.local_model_management.readiness import inspect_local_model_gateway
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.providers.readiness import (
    GovernedProviderInvocationReadiness,
    ProviderCostGovernorBinding,
    ProviderCredentialReadinessPosture,
    ProviderCredentialValidationReadiness,
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
    control_center_route_count: int = Field(49, ge=0)
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

    model_config = ConfigDict(extra="forbid")


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
    control_center_route_count: int = 49,
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
        plugin_governance_summary=PluginGovernanceSummary(),
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
    return ProviderCredentialReadinessSummary(
        vault_adapter_readiness=build_provider_credential_vault_adapter_readiness(vault_capabilities),
        enrollment_readiness=ProviderCredentialEnrollmentReadiness(),
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
