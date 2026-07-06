from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.dashboard import (
    ProviderCredentialReadinessSummary,
    build_provider_credential_readiness_summary,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.local_model_management.gateway import (
    DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
)
from ultimate_ai_agent.core.local_model_management.inventory import (
    inspect_local_model_inventory,
)
from ultimate_ai_agent.core.local_model_management.readiness import (
    LocalModelGatewayReadiness,
    inspect_local_model_gateway,
)
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelPrivacyClass,
    ModelProviderKind,
    ModelRouteDecision,
    ModelRouteRequest,
    ModelRouter,
    ModelRoutingPolicy,
    ModelTaskCapability,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.providers.catalog import (
    ProviderCatalog,
    build_provider_setup_guide_catalog,
)
from ultimate_ai_agent.core.providers.credential_validation import (
    PROVIDER_CREDENTIAL_VALIDATION_ENDPOINT_REF,
    PROVIDER_CREDENTIAL_VALIDATION_NETWORK_SCOPE_REF,
    PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
)
from ultimate_ai_agent.core.providers.invocation import (
    SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
    SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF,
    SECOND_TINY_LIVE_PROVIDER_MODEL_NAME_REF,
    SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
    SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
    SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
    SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
    TINY_LIVE_PROVIDER_ADAPTER_REF,
    TINY_LIVE_PROVIDER_ENDPOINT_REF,
    TINY_LIVE_PROVIDER_MODEL_NAME_REF,
    TINY_LIVE_PROVIDER_TRANSPORT_REF,
    TINY_PROVIDER_INVOCATION_MODEL_REF,
    TINY_PROVIDER_INVOCATION_POLICY_REF,
    TINY_PROVIDER_INVOCATION_PROVIDER_REF,
)
from ultimate_ai_agent.core.providers.role_evidence import (
    RoleBasedModelProviderEvidenceReadModel,
    build_role_based_model_provider_evidence,
)
from ultimate_ai_agent.core.runtime_gateway.profile_isolation import (
    RUNTIME_PROFILE_ISOLATION_ROUTE_REF,
    build_runtime_profile_isolation_read_model,
)
from ultimate_ai_agent.core.web_access.runtime_authority import (
    build_web_runtime_authority_contract,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


MODEL_PROVIDER_CONTROL_PLANE_CONTRACT_REF = (
    "contract-ref:model-provider-control-plane:v1"
)
MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF = (
    "GET /control-center/providers/runtime-control-plane"
)
MODEL_PROVIDER_CONTROL_PLANE_CLI_REF = "scripts/inspect_model_provider_control_plane.py"
MODEL_PROVIDER_CONTROL_PLANE_VERIFIER_REF = (
    "scripts/verify_model_provider_control_plane.py"
)
MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF = (
    "contract-ref:goatcitadel-catchup-model-provider-research-posture:v1"
)
MODEL_PROVIDER_RESEARCH_POSTURE_SOURCE = (
    "python_core_goatcitadel_catchup_model_provider_research_posture"
)
MODEL_PROVIDER_RESEARCH_POSTURE_VERIFIER_REF = (
    "scripts/verify_uaa_goatcitadel_catchup_model_provider_research.py"
)
DELEGATED_RUNTIME_MODEL_CATALOG_CONTRACT_REF = (
    "contract-ref:hermes-runtime-model-provider-catalog:v1"
)
DELEGATED_RUNTIME_MODEL_CATALOG_VERIFIER_REF = (
    "scripts/verify_hermes_runtime_adoption_phase_07.py"
)
MODEL_SLOT_POSTURE_CONTRACT_REF = "contract-ref:hermes-runtime-model-slot-posture:v1"
MODEL_SLOT_POSTURE_TRUST_LANE_REF = "trust-lane:model-slot-posture"
MODEL_SLOT_POSTURE_VERIFIER_REF = "scripts/verify_hermes_runtime_adoption_phase_08.py"


class ModelProviderAuthoritySummary(BaseModel):
    status: Literal["governed_exact_lanes_only"] = "governed_exact_lanes_only"
    broad_provider_runtime_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    live_provider_network_call_enabled_by_default: bool = False
    exact_tiny_provider_lane_available: bool = True
    exact_tiny_provider_lane_requires_approval: bool = True
    exact_credential_validation_lane_available: bool = True
    exact_credential_validation_requires_approval: bool = True
    provider_router_execution_enabled: bool = False
    provider_router_dry_run_available: bool = True
    model_router_execution_enabled: bool = False
    model_router_trace_available: bool = True
    local_llama_cpp_gateway_available: bool = True
    local_llama_cpp_lifecycle_contract_available: bool = True
    local_llama_cpp_process_started_by_control_plane: bool = False
    shell_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False
    raw_prompt_response_provider_payload_persisted: bool = False
    safe_summary: str = (
        "Model/provider handling is wired as governed exact lanes, safe refs, "
        "cost hooks, local lifecycle posture, and router traces. Broad runtime "
        "provider execution remains blocked."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def authority_summary_must_remain_governed(self) -> Any:
        denied = [
            self.broad_provider_runtime_enabled,
            self.provider_sdk_call_enabled,
            self.live_provider_network_call_enabled_by_default,
            self.provider_router_execution_enabled,
            self.model_router_execution_enabled,
            self.local_llama_cpp_process_started_by_control_plane,
            self.shell_execution_enabled,
            self.background_autonomy_enabled,
            self.production_authority_enabled,
            self.raw_prompt_response_provider_payload_persisted,
        ]
        required = [
            self.exact_tiny_provider_lane_available,
            self.exact_tiny_provider_lane_requires_approval,
            self.exact_credential_validation_lane_available,
            self.exact_credential_validation_requires_approval,
            self.provider_router_dry_run_available,
            self.model_router_trace_available,
            self.local_llama_cpp_gateway_available,
            self.local_llama_cpp_lifecycle_contract_available,
        ]
        if any(denied) or not all(required):
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_AUTHORITY_DRIFT")
        return self


class ProviderAdapterRuntimePosture(BaseModel):
    adapter_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    model_ref: str = Field(..., min_length=1)
    model_name_ref: str = Field(..., min_length=1)
    policy_ref: str = Field(..., min_length=1)
    endpoint_ref: str = Field(..., min_length=1)
    transport_ref: str = Field(..., min_length=1)
    status: Literal["exact_lane_wired_disabled_by_default"] = (
        "exact_lane_wired_disabled_by_default"
    )
    provider_sdk_call_enabled: bool = False
    network_call_enabled_by_default: bool = False
    network_call_allowed_inside_exact_adapter: bool = True
    credential_ref_required: bool = True
    exact_approval_required: bool = True
    cost_governor_required: bool = True
    receipt_store_required_before_network: bool = True
    redirects_blocked: bool = True
    prompt_persistence_allowed: bool = False
    response_persistence_allowed: bool = False
    provider_payload_persistence_allowed: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def adapter_must_remain_exact_lane_only(self) -> Any:
        denied = [
            self.provider_sdk_call_enabled,
            self.network_call_enabled_by_default,
            self.prompt_persistence_allowed,
            self.response_persistence_allowed,
            self.provider_payload_persistence_allowed,
        ]
        required = [
            self.network_call_allowed_inside_exact_adapter,
            self.credential_ref_required,
            self.exact_approval_required,
            self.cost_governor_required,
            self.receipt_store_required_before_network,
            self.redirects_blocked,
        ]
        if any(denied) or not all(required):
            raise ValueError("MODEL_PROVIDER_ADAPTER_POSTURE_AUTHORITY_DRIFT")
        return self


class ProviderSecretStatusPosture(BaseModel):
    status: Literal["safe_refs_only"] = "safe_refs_only"
    vault_adapter_status: str
    validation_readiness_status: str
    enrollment_status: str
    credential_ref_statuses: dict[str, str]
    secret_material_visible: bool = False
    secret_material_persisted_by_repo: bool = False
    transient_secret_resolution_required_for_exact_lanes: bool = True
    raw_key_collection_enabled: bool = False
    safe_summary: str = (
        "Provider secrets are represented by safe refs and readiness states. "
        "Credential material is not collected, stored, or displayed by the "
        "Control Center read model."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def secret_status_must_not_expose_secret_material(self) -> Any:
        if (
            self.secret_material_visible
            or self.secret_material_persisted_by_repo
            or self.raw_key_collection_enabled
            or not self.transient_secret_resolution_required_for_exact_lanes
        ):
            raise ValueError("MODEL_PROVIDER_SECRET_STATUS_AUTHORITY_DRIFT")
        return self


class ProviderNetworkAllowlistPosture(BaseModel):
    status: Literal["exact_endpoint_refs_only"] = "exact_endpoint_refs_only"
    allowlist_refs: list[str]
    endpoint_refs: list[str]
    transport_refs: list[str]
    default_network_denied: bool = True
    broad_web_fetch_enabled: bool = False
    provider_sdk_network_enabled: bool = False
    redirects_blocked: bool = True
    post_mutation_scope_enabled: bool = False
    safe_summary: str = (
        "Only reviewed endpoint refs for exact provider lanes are visible. "
        "No broad web fetch, provider SDK network, redirects, or mutation "
        "scope is granted by this read model."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def network_must_remain_exact_allowlist_only(self) -> Any:
        if (
            not self.default_network_denied
            or self.broad_web_fetch_enabled
            or self.provider_sdk_network_enabled
            or not self.redirects_blocked
            or self.post_mutation_scope_enabled
            or not self.allowlist_refs
            or not self.endpoint_refs
        ):
            raise ValueError("MODEL_PROVIDER_NETWORK_ALLOWLIST_AUTHORITY_DRIFT")
        return self


class ModelMetadataDiscoveryPosture(BaseModel):
    status: Literal["static_metadata_and_local_inventory"] = (
        "static_metadata_and_local_inventory"
    )
    provider_catalog_ref: str
    provider_count: int = Field(..., ge=0)
    provider_model_refs: list[str]
    local_inventory_status: str
    local_inventory_model_ref_count: int = Field(..., ge=0)
    local_gateway_model_ref: str
    live_provider_model_discovery_enabled: bool = False
    automatic_pricing_fetch_enabled: bool = False
    runtime_provider_metadata_fetch_enabled: bool = False
    safe_summary: str = (
        "Model metadata comes from reviewed static provider catalog refs, "
        "safe local inventory refs, and the local gateway model ref. Live "
        "provider discovery remains blocked unless an exact lane approves it."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def metadata_discovery_must_remain_static_or_local(self) -> Any:
        if (
            self.live_provider_model_discovery_enabled
            or self.automatic_pricing_fetch_enabled
            or self.runtime_provider_metadata_fetch_enabled
        ):
            raise ValueError("MODEL_PROVIDER_DISCOVERY_AUTHORITY_DRIFT")
        if not self.provider_model_refs or not self.local_gateway_model_ref:
            raise ValueError("MODEL_PROVIDER_DISCOVERY_REFS_REQUIRED")
        return self


class DelegatedRuntimeModelAvailabilityRecord(BaseModel):
    runtime_ref: str = Field(..., min_length=1)
    runtime_profile_ref: str = Field(..., min_length=1)
    delegated_runtime_profile_ref: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    model_ref: str = Field(..., min_length=1)
    display_label: str = Field(..., min_length=1)
    runtime_availability_status: Literal[
        "runtime_reports_available",
        "runtime_reports_planned",
        "local_gateway_metadata_available",
    ]
    uaa_invocation_posture: Literal[
        "blocked_no_exact_invocation_lane",
        "blocked_profile_not_configured",
        "metadata_only_existing_lane_separate",
    ]
    cost_metadata_status: Literal[
        "static_cost_metadata_only",
        "local_hardware_cost_posture_only",
        "cost_unknown_blocks_use",
    ]
    latency_metadata_status: Literal[
        "static_latency_label_only",
        "local_gateway_readiness_only",
        "latency_unknown_blocks_use",
    ]
    source_ref: str = Field(..., min_length=1)
    cost_posture_ref: str = Field(..., min_length=1)
    latency_posture_ref: str = Field(..., min_length=1)
    runtime_reported_available: bool
    uaa_invocation_allowed: bool = False
    provider_sdk_call_enabled: bool = False
    live_provider_discovery_performed: bool = False
    live_provider_network_call_performed: bool = False
    credential_collection_enabled: bool = False
    credential_material_visible: bool = False
    billing_authority_granted: bool = False
    model_output_authority_enabled: bool = False
    raw_provider_payload_persisted: bool = False
    safe_summary: str
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def availability_record_must_not_grant_invocation(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError(
                "DELEGATED_RUNTIME_MODEL_CATALOG_SECRET_LIKE_VALUE_REJECTED"
            )
        denied = [
            self.uaa_invocation_allowed,
            self.provider_sdk_call_enabled,
            self.live_provider_discovery_performed,
            self.live_provider_network_call_performed,
            self.credential_collection_enabled,
            self.credential_material_visible,
            self.billing_authority_granted,
            self.model_output_authority_enabled,
            self.raw_provider_payload_persisted,
        ]
        if any(denied):
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_AUTHORITY_DRIFT")
        if not self.blocked_authority_refs:
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_BLOCKERS_REQUIRED")
        return self


class DelegatedRuntimeModelCatalogPosture(BaseModel):
    schema_version: Literal["delegated_runtime_model_catalog.v1"] = (
        "delegated_runtime_model_catalog.v1"
    )
    contract_ref: str = DELEGATED_RUNTIME_MODEL_CATALOG_CONTRACT_REF
    status: Literal["read_only_runtime_model_availability"] = (
        "read_only_runtime_model_availability"
    )
    route_ref: str = MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    cli_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CLI_REF
    runtime_profiles_route_ref: str = RUNTIME_PROFILE_ISOLATION_ROUTE_REF
    provider_catalog_ref: str
    model_count: int = Field(..., ge=0)
    runtime_profile_count: int = Field(..., ge=0)
    runtime_reported_available_count: int = Field(..., ge=0)
    uaa_authorized_model_count: int = 0
    records: list[DelegatedRuntimeModelAvailabilityRecord]
    runtime_says_available_is_not_authority: bool = True
    uaa_may_invoke_any_listed_model: bool = False
    static_cost_metadata_only: bool = True
    static_latency_metadata_only: bool = True
    live_provider_discovery_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    remote_model_call_enabled: bool = False
    credential_collection_enabled: bool = False
    billing_authority_granted: bool = False
    model_output_authority_enabled: bool = False
    proof_refs: list[str] = Field(
        default_factory=lambda: [
            "proof-ref:hermes-runtime-adoption:phase-07:model-provider-catalog",
            "proof-ref:model-provider-control-plane:read-model",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/runtime/UAA_HERMES_RUNTIME_MODEL_PROVIDER_CATALOG.md",
            "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [DELEGATED_RUNTIME_MODEL_CATALOG_VERIFIER_REF]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:model-provider:runtime-availability-is-not-invocation",
            "blocked-state:model-provider:provider-sdk-calls",
            "blocked-state:model-provider:remote-model-calls-by-control-plane",
            "blocked-state:model-provider:credential-collection",
            "blocked-state:model-provider:billing-authority",
            "blocked-state:model-provider:model-output-as-authority",
            "blocked-state:model-provider:live-provider-discovery",
        ]
    )
    safe_summary: str = (
        "Delegated runtime model availability is displayed as read-only "
        "metadata. Runtime-reported availability is separated from UAA "
        "invocation authority, which remains blocked by this catalog."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def catalog_must_remain_read_only_metadata(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError(
                "DELEGATED_RUNTIME_MODEL_CATALOG_SECRET_LIKE_VALUE_REJECTED"
            )
        if self.model_count != len(self.records):
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_COUNT_DRIFT")
        if self.runtime_reported_available_count != len(
            [record for record in self.records if record.runtime_reported_available]
        ):
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_AVAILABLE_COUNT_DRIFT")
        if self.uaa_authorized_model_count != 0:
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_AUTHORIZED_COUNT_DENIED")
        denied = [
            self.uaa_may_invoke_any_listed_model,
            self.live_provider_discovery_enabled,
            self.provider_sdk_call_enabled,
            self.remote_model_call_enabled,
            self.credential_collection_enabled,
            self.billing_authority_granted,
            self.model_output_authority_enabled,
        ]
        required = [
            self.runtime_says_available_is_not_authority,
            self.static_cost_metadata_only,
            self.static_latency_metadata_only,
        ]
        if any(denied) or not all(required):
            raise ValueError("DELEGATED_RUNTIME_MODEL_CATALOG_AUTHORITY_DRIFT")
        return self


class ProviderCostHookPosture(BaseModel):
    status: Literal["cost_governor_receipt_bound"] = "cost_governor_receipt_bound"
    cost_governor_posture_ref: str
    cost_governor_decision_ref: str
    cost_estimate_refs_required: bool = True
    budget_decision_refs_required: bool = True
    max_approved_usd_refs_required: bool = True
    expected_receipt_refs_required: bool = True
    actual_usage_cost_refs_required: bool = True
    unknown_paid_cost_blocks: bool = True
    incomplete_actual_cost_blocks_further_use: bool = True
    provider_spend_authority_granted: bool = False
    safe_summary: str = (
        "Provider runtime use is receipt-bound and CostGovernor-bound. "
        "Unknown paid cost blocks use, and incomplete actual cost blocks "
        "further use until reviewed."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def cost_hooks_must_remain_bound(self) -> Any:
        required = [
            self.cost_estimate_refs_required,
            self.budget_decision_refs_required,
            self.max_approved_usd_refs_required,
            self.expected_receipt_refs_required,
            self.actual_usage_cost_refs_required,
            self.unknown_paid_cost_blocks,
            self.incomplete_actual_cost_blocks_further_use,
        ]
        if not all(required) or self.provider_spend_authority_granted:
            raise ValueError("MODEL_PROVIDER_COST_HOOK_AUTHORITY_DRIFT")
        return self


class LocalLlamaCppLifecyclePosture(BaseModel):
    status: Literal["local_loopback_lifecycle_governed"] = (
        "local_loopback_lifecycle_governed"
    )
    supervisor_contract_ref: str = "contract-ref:llama-cpp-supervisor:m163"
    gateway_contract_ref: str = "contract-ref:llama-cpp-gateway:m164"
    gateway_readiness: LocalModelGatewayReadiness
    model_ref: str = f"model-ref:local:{DEFAULT_UAA_LLAMA_CPP_MODEL_ID}"
    loopback_only: bool = True
    structured_argv_only: bool = True
    shell_string_allowed: bool = False
    process_start_performed_by_read_model: bool = False
    model_call_performed_by_read_model: bool = False
    raw_local_path_returned: bool = False
    raw_log_stored: bool = False
    cli_inspection_refs: list[str] = Field(
        default_factory=lambda: [
            "scripts/dev/uaa_local_model.py local-model status --json",
            "scripts/inspect_local_model_runtime.py",
        ]
    )
    safe_summary: str = (
        "llama.cpp lifecycle support is visible as governed local loopback "
        "readiness. This read model does not start processes, call models, "
        "return local paths, or store raw logs."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def local_lifecycle_must_not_start_or_call_models(self) -> Any:
        if (
            not self.loopback_only
            or not self.structured_argv_only
            or self.shell_string_allowed
            or self.process_start_performed_by_read_model
            or self.model_call_performed_by_read_model
            or self.raw_local_path_returned
            or self.raw_log_stored
        ):
            raise ValueError("MODEL_PROVIDER_LOCAL_LLAMA_AUTHORITY_DRIFT")
        return self


class ModelRouterTracePosture(BaseModel):
    status: Literal["trace_only_no_execution"] = "trace_only_no_execution"
    trace_ref: str
    decision: ModelRouteDecision
    provider_router_trace_ref: str
    provider_router_status: str
    selected_profile_ref: str | None
    selected_model_ref: str | None
    candidate_profile_refs: list[str]
    rejected_profile_refs: list[str]
    reason_codes: list[str]
    model_execution_performed: bool = False
    provider_execution_performed: bool = False
    provider_sdk_call_performed: bool = False
    prompt_content_persisted: bool = False
    response_content_persisted: bool = False
    safe_summary: str = (
        "ModelRouter trace is deterministic route metadata only; no model, "
        "provider SDK, provider network, prompt persistence, or response "
        "persistence is performed."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def router_trace_must_not_execute(self) -> Any:
        if (
            self.model_execution_performed
            or self.provider_execution_performed
            or self.provider_sdk_call_performed
            or self.prompt_content_persisted
            or self.response_content_persisted
        ):
            raise ValueError("MODEL_PROVIDER_ROUTER_TRACE_AUTHORITY_DRIFT")
        if not self.reason_codes:
            raise ValueError("MODEL_PROVIDER_ROUTER_TRACE_REASON_CODES_REQUIRED")
        return self


class ModelSlotPostureRecord(BaseModel):
    slot_ref: str = Field(..., min_length=1)
    slot_role: Literal[
        "main_thinking",
        "summarization",
        "title",
        "approval_scoring",
        "compression",
        "retrieval",
        "vision",
        "review",
    ]
    display_label: str = Field(..., min_length=1)
    intended_provider_ref: str = Field(..., min_length=1)
    intended_model_ref: str = Field(..., min_length=1)
    source_profile_ref: str = Field(..., min_length=1)
    delegated_runtime_profile_ref: str = Field(..., min_length=1)
    configured_status: Literal[
        "configured_metadata_only",
        "planned_not_configured",
        "runtime_reported_available_not_authorized",
    ]
    uaa_execution_posture: Literal[
        "blocked_no_exact_model_authority",
        "blocked_missing_runtime_profile",
        "metadata_only_existing_lane_separate",
    ]
    provider_readiness_ref: str = Field(..., min_length=1)
    cost_posture_ref: str = Field(..., min_length=1)
    latency_posture_ref: str = Field(..., min_length=1)
    route_decision_trace_ref: str = Field(..., min_length=1)
    model_output_truth_ref: str = Field(..., min_length=1)
    warning_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    live_auxiliary_call_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    runtime_selection_mutation_enabled: bool = False
    hidden_model_routing_enabled: bool = False
    route_decision_trace_required: bool = True
    cost_estimate_required: bool = True
    approval_profile_mapping_required: bool = True
    model_output_truth_envelope_required: bool = True
    receipt_required_before_execution: bool = True
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def slot_record_must_remain_metadata_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("MODEL_SLOT_POSTURE_SECRET_LIKE_VALUE_REJECTED")
        denied = [
            self.live_auxiliary_call_enabled,
            self.provider_sdk_call_enabled,
            self.runtime_selection_mutation_enabled,
            self.hidden_model_routing_enabled,
            self.raw_prompt_persisted,
            self.raw_response_persisted,
        ]
        required = [
            self.route_decision_trace_required,
            self.cost_estimate_required,
            self.approval_profile_mapping_required,
            self.model_output_truth_envelope_required,
            self.receipt_required_before_execution,
        ]
        if any(denied) or not all(required):
            raise ValueError("MODEL_SLOT_POSTURE_AUTHORITY_DRIFT")
        if not self.blocked_authority_refs:
            raise ValueError("MODEL_SLOT_POSTURE_BLOCKERS_REQUIRED")
        return self


class ModelSlotPostureReadModel(BaseModel):
    schema_version: Literal["hermes_runtime_model_slot_posture.v1"] = (
        "hermes_runtime_model_slot_posture.v1"
    )
    contract_ref: str = MODEL_SLOT_POSTURE_CONTRACT_REF
    status: Literal["read_only_model_slot_intent"] = "read_only_model_slot_intent"
    route_ref: str = MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    cli_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CLI_REF
    trust_lane_ref: str = MODEL_SLOT_POSTURE_TRUST_LANE_REF
    provider_readiness_ref: str = (
        "control-center-dashboard-field:provider_credential_readiness"
    )
    delegated_model_catalog_ref: str = DELEGATED_RUNTIME_MODEL_CATALOG_CONTRACT_REF
    slot_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    records: list[ModelSlotPostureRecord]
    main_slot_ref: str = "model-slot-ref:uaa:main-thinking"
    auxiliary_slot_refs: list[str] = Field(default_factory=list)
    live_auxiliary_calls_enabled: bool = False
    provider_sdk_use_enabled: bool = False
    runtime_selection_mutation_enabled: bool = False
    hidden_model_routing_enabled: bool = False
    raw_prompt_persistence_enabled: bool = False
    raw_response_persistence_enabled: bool = False
    route_decision_trace_required: bool = True
    cost_estimate_required: bool = True
    approval_profile_mapping_required: bool = True
    model_output_truth_envelope_required: bool = True
    receipts_required_before_execution: bool = True
    proof_refs: list[str] = Field(
        default_factory=lambda: [
            "proof-ref:hermes-runtime-adoption:phase-08:model-slot-posture",
            "proof-ref:model-provider-control-plane:model-slot-posture",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/runtime/UAA_HERMES_RUNTIME_MODEL_SLOT_POSTURE.md",
            "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
        ]
    )
    verifier_refs: list[str] = Field(default_factory=lambda: [MODEL_SLOT_POSTURE_VERIFIER_REF])
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:model-slot:live-auxiliary-model-calls",
            "blocked-state:model-slot:provider-sdk-use",
            "blocked-state:model-slot:runtime-selection-mutation",
            "blocked-state:model-slot:hidden-model-routing",
            "blocked-state:model-slot:raw-prompt-persistence",
            "blocked-state:model-slot:raw-response-persistence",
        ]
    )
    safe_summary: str = (
        "Main and auxiliary model slots are visible as backend-owned intent "
        "metadata only. Slot routing does not call providers, mutate runtime "
        "selection, or hide model routing."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def slot_posture_must_remain_read_only(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("MODEL_SLOT_POSTURE_SECRET_LIKE_VALUE_REJECTED")
        denied = [
            self.live_auxiliary_calls_enabled,
            self.provider_sdk_use_enabled,
            self.runtime_selection_mutation_enabled,
            self.hidden_model_routing_enabled,
            self.raw_prompt_persistence_enabled,
            self.raw_response_persistence_enabled,
        ]
        required = [
            self.route_decision_trace_required,
            self.cost_estimate_required,
            self.approval_profile_mapping_required,
            self.model_output_truth_envelope_required,
            self.receipts_required_before_execution,
        ]
        if any(denied) or not all(required):
            raise ValueError("MODEL_SLOT_POSTURE_AUTHORITY_DRIFT")
        if self.slot_count != len(self.records):
            raise ValueError("MODEL_SLOT_POSTURE_COUNT_DRIFT")
        if self.warning_count != sum(bool(record.warning_refs) for record in self.records):
            raise ValueError("MODEL_SLOT_POSTURE_WARNING_COUNT_DRIFT")
        if self.main_slot_ref not in {record.slot_ref for record in self.records}:
            raise ValueError("MODEL_SLOT_POSTURE_MAIN_SLOT_MISSING")
        if set(self.auxiliary_slot_refs) != {
            record.slot_ref for record in self.records if record.slot_ref != self.main_slot_ref
        }:
            raise ValueError("MODEL_SLOT_POSTURE_AUXILIARY_SLOT_DRIFT")
        return self


class ModelProviderResearchProviderPosture(BaseModel):
    provider_id: str = Field(..., min_length=1)
    provider_label: str = Field(..., min_length=1)
    provider_kind: str = Field(..., min_length=1)
    local_remote_posture: Literal[
        "remote_provider_reference", "local_runtime_reference"
    ]
    status: Literal[
        "reference_only",
        "blocked_missing_refs",
        "approval_required_exact_lane",
    ]
    credential_readiness_status: str = Field(..., min_length=1)
    cost_latency_metadata_status: Literal[
        "static_cost_metadata_only",
        "local_inventory_metadata_only",
    ] = "static_cost_metadata_only"
    supported_authority_mode: Literal[
        "guidance_only",
        "exact_lane_requires_approval",
        "local_loopback_metadata_only",
    ] = "guidance_only"
    blocked_reason_ref: str = Field(..., min_length=1)
    last_safe_diagnostic_receipt_ref: str = Field(..., min_length=1)
    operator_next_step: str = Field(..., min_length=1)
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    credential_material_visible: bool = False
    provider_output_authority_enabled: bool = False
    live_metadata_discovery_enabled: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def provider_posture_must_remain_metadata_only(self) -> Any:
        denied = [
            self.provider_sdk_call_enabled,
            self.model_invocation_enabled,
            self.credential_material_visible,
            self.provider_output_authority_enabled,
            self.live_metadata_discovery_enabled,
        ]
        if any(denied):
            raise ValueError("MODEL_PROVIDER_RESEARCH_PROVIDER_AUTHORITY_DRIFT")
        return self


class ModelOutputTruthPosture(BaseModel):
    status: Literal["proposal_and_evidence_not_authority"] = (
        "proposal_and_evidence_not_authority"
    )
    model_output_is_proposal: bool = True
    model_output_is_evidence_candidate: bool = True
    generated_text_is_verified_fact: bool = False
    verified_fact_refs_required: bool = True
    uncertainty_unknowns_required: bool = True
    memory_write_from_model_output_enabled: bool = False
    action_authority_from_model_output_enabled: bool = False
    context_injection_from_model_output_enabled: bool = False
    connector_write_from_model_output_enabled: bool = False
    production_authority_from_model_output_enabled: bool = False
    truth_boundary_ref: str = "truth-boundary-ref:model-output:not-authority"
    safe_summary: str = (
        "Model output can be proposal text or evidence candidate only. "
        "Verified facts require separate evidence refs, and model output cannot "
        "grant memory, action, context, connector, or production authority."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def model_output_must_not_be_authority(self) -> Any:
        denied = [
            self.generated_text_is_verified_fact,
            self.memory_write_from_model_output_enabled,
            self.action_authority_from_model_output_enabled,
            self.context_injection_from_model_output_enabled,
            self.connector_write_from_model_output_enabled,
            self.production_authority_from_model_output_enabled,
        ]
        required = [
            self.model_output_is_proposal,
            self.model_output_is_evidence_candidate,
            self.verified_fact_refs_required,
            self.uncertainty_unknowns_required,
        ]
        if any(denied) or not all(required):
            raise ValueError("MODEL_OUTPUT_TRUTH_AUTHORITY_DRIFT")
        return self


class ExternalInformationResearchPosture(BaseModel):
    status: Literal["web_access_gateway_deny_by_default"] = (
        "web_access_gateway_deny_by_default"
    )
    web_runtime_authority_contract_ref: str
    web_access_gateway_required: bool = True
    default_policy_denied: bool = True
    fetched_content_untrusted: bool = True
    fetched_content_instruction_authority_enabled: bool = False
    source_metadata_required: bool = True
    audit_record_required: bool = True
    live_web_fetch_enabled_by_control_plane: bool = False
    browser_observe_enabled_by_control_plane: bool = False
    browser_action_enabled_by_control_plane: bool = False
    provider_search_enabled_by_control_plane: bool = False
    context_injection_from_external_content_enabled: bool = False
    memory_write_from_external_content_enabled: bool = False
    allowed_current_lane_refs: list[str] = Field(
        default_factory=lambda: [
            "lane-ref:web-evidence:allowlisted-https-get-through-web-access-gateway"
        ]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:web-access:no-unrestricted-web-fetch",
            "blocked-state:web-access:no-provider-search-calls",
            "blocked-state:web-access:no-browser-observe-by-control-plane",
            "blocked-state:web-access:no-browser-actions",
            "blocked-state:web-access:no-context-injection",
            "blocked-state:web-access:no-memory-write",
            "blocked-state:web-access:no-production-authority",
        ]
    )
    safe_summary: str = (
        "External information remains WebAccessGateway governed and deny-by-default. "
        "Fetched content is untrusted evidence, never instructions or authority."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def external_information_must_remain_deny_by_default(self) -> Any:
        denied = [
            self.fetched_content_instruction_authority_enabled,
            self.live_web_fetch_enabled_by_control_plane,
            self.browser_observe_enabled_by_control_plane,
            self.browser_action_enabled_by_control_plane,
            self.provider_search_enabled_by_control_plane,
            self.context_injection_from_external_content_enabled,
            self.memory_write_from_external_content_enabled,
        ]
        required = [
            self.web_access_gateway_required,
            self.default_policy_denied,
            self.fetched_content_untrusted,
            self.source_metadata_required,
            self.audit_record_required,
        ]
        if any(denied) or not all(required):
            raise ValueError("EXTERNAL_INFORMATION_RESEARCH_AUTHORITY_DRIFT")
        if not self.allowed_current_lane_refs or not self.blocked_authority_refs:
            raise ValueError("EXTERNAL_INFORMATION_RESEARCH_REFS_REQUIRED")
        return self


class ModelProviderResearchPosture(BaseModel):
    schema_version: Literal["model_provider_research_posture.v1"] = (
        "model_provider_research_posture.v1"
    )
    contract_ref: str = MODEL_PROVIDER_RESEARCH_POSTURE_CONTRACT_REF
    source: str = MODEL_PROVIDER_RESEARCH_POSTURE_SOURCE
    status: Literal["metadata_read_model_wired"] = "metadata_read_model_wired"
    route_ref: str = MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    cli_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CLI_REF
    provider_count: int = Field(..., ge=0)
    provider_postures: list[ModelProviderResearchProviderPosture]
    model_output_truth: ModelOutputTruthPosture = Field(
        default_factory=ModelOutputTruthPosture
    )
    external_information: ExternalInformationResearchPosture
    proof_refs: list[str] = Field(
        default_factory=lambda: [
            "proof-ref:goatcitadel-catchup:model-provider-research-posture",
            "proof-ref:model-provider-control-plane:read-model",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/control_center/UAA_GOATCITADEL_CATCHUP_MODEL_PROVIDER_RESEARCH.md",
            "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
            "docs/network/WEB_ACCESS_GATEWAY.md",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [
            MODEL_PROVIDER_RESEARCH_POSTURE_VERIFIER_REF,
            MODEL_PROVIDER_CONTROL_PLANE_VERIFIER_REF,
        ]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:model-provider:provider-sdk-calls",
            "blocked-state:model-provider:remote-model-calls-by-control-plane",
            "blocked-state:model-provider:model-output-as-authority",
            "blocked-state:model-provider:credential-material-display",
            "blocked-state:web-access:live-fetch-by-control-plane",
            "blocked-state:web-access:browser-automation",
            "blocked-state:model-provider:memory-action-context-escalation",
            "blocked-state:model-provider:production-authority",
        ]
    )
    next_safe_action: str = (
        "Use the control-plane CLI/API/UI to inspect readiness and exact blockers; "
        "promote live calls or external research only through a later exact lane."
    )
    provider_sdk_call_enabled: bool = False
    remote_model_call_enabled: bool = False
    live_web_fetch_enabled: bool = False
    browser_automation_enabled: bool = False
    credential_entry_enabled: bool = False
    memory_write_authorized: bool = False
    action_execution_authorized: bool = False
    context_injection_authorized: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def research_posture_must_remain_safe(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError(
                "MODEL_PROVIDER_RESEARCH_POSTURE_SECRET_LIKE_VALUE_REJECTED"
            )
        denied = [
            self.provider_sdk_call_enabled,
            self.remote_model_call_enabled,
            self.live_web_fetch_enabled,
            self.browser_automation_enabled,
            self.credential_entry_enabled,
            self.memory_write_authorized,
            self.action_execution_authorized,
            self.context_injection_authorized,
            self.production_authority_enabled,
            self.broad_autonomy_enabled,
        ]
        if any(denied):
            raise ValueError("MODEL_PROVIDER_RESEARCH_POSTURE_AUTHORITY_DRIFT")
        if self.provider_count != len(self.provider_postures):
            raise ValueError("MODEL_PROVIDER_RESEARCH_POSTURE_PROVIDER_COUNT_DRIFT")
        if not self.provider_postures:
            raise ValueError("MODEL_PROVIDER_RESEARCH_POSTURE_PROVIDER_ROWS_REQUIRED")
        return self


class ModelProviderControlPlaneReadModel(BaseModel):
    schema_version: Literal["model_provider_control_plane.v1"] = (
        "model_provider_control_plane.v1"
    )
    contract_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CONTRACT_REF
    route_ref: str = MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    cli_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CLI_REF
    status: Literal["governed_control_plane_wired"] = "governed_control_plane_wired"
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    authority: ModelProviderAuthoritySummary
    provider_adapters: list[ProviderAdapterRuntimePosture]
    secret_status: ProviderSecretStatusPosture
    network_allowlists: ProviderNetworkAllowlistPosture
    model_metadata_discovery: ModelMetadataDiscoveryPosture
    cost_hooks: ProviderCostHookPosture
    local_llama_cpp_lifecycle: LocalLlamaCppLifecyclePosture
    router_traces: list[ModelRouterTracePosture]
    delegated_runtime_model_catalog: DelegatedRuntimeModelCatalogPosture
    model_slot_posture: ModelSlotPostureReadModel
    role_provider_evidence: RoleBasedModelProviderEvidenceReadModel
    model_provider_research_posture: ModelProviderResearchPosture
    credential_readiness_ref: str = (
        "control-center-dashboard-field:provider_credential_readiness"
    )
    provider_catalog_ref: str
    exact_lane_route_refs: list[str] = Field(
        default_factory=lambda: [
            "POST /control-center/providers/exact-approved-lanes/tiny",
            "POST /control-center/providers/credentials/validate",
            "POST /control-center/providers/router/dry-run",
        ]
    )
    proof_refs: list[str] = Field(
        default_factory=lambda: [
            "proof-ref:model-provider-control-plane:read-model",
            "proof-ref:model-provider-control-plane:router-traces",
            "proof-ref:model-provider-control-plane:cost-hooks",
            "proof-ref:goatcitadel-catchup:model-provider-research-posture",
            "proof-ref:hermes-runtime-adoption:phase-07:model-provider-catalog",
            "proof-ref:hermes-runtime-adoption:phase-08:model-slot-posture",
        ]
    )
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: [
            "blocked-state:model-provider:broad-provider-runtime",
            "blocked-state:model-provider:provider-sdk-calls",
            "blocked-state:model-provider:network-by-default",
            "blocked-state:model-provider:raw-prompt-response-persistence",
            "blocked-state:model-provider:background-autonomy",
            "blocked-state:model-provider:production-authority",
        ]
    )
    docs_refs: list[str] = Field(
        default_factory=lambda: [
            "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
            "docs/runtime/UAA_HERMES_RUNTIME_MODEL_PROVIDER_CATALOG.md",
            "docs/runtime/UAA_HERMES_RUNTIME_MODEL_SLOT_POSTURE.md",
            "docs/control_center/UAA_GOATCITADEL_CATCHUP_MODEL_PROVIDER_RESEARCH.md",
            "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
            "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [
            MODEL_PROVIDER_CONTROL_PLANE_VERIFIER_REF,
            MODEL_PROVIDER_RESEARCH_POSTURE_VERIFIER_REF,
        ]
    )
    safe_summary: str = (
        "Backend-owned model/provider control plane unifies provider adapters, "
        "secret posture, endpoint allowlist refs, metadata discovery, cost "
        "hooks, llama.cpp lifecycle posture, and router traces without "
        "granting broad runtime provider authority."
    )

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    @model_validator(mode="after")
    def control_plane_must_be_safe_and_backend_owned(self) -> Any:
        dump = self.model_dump(mode="json")
        if contains_secret_like(dump) or contains_obvious_secret(dump):
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_SECRET_LIKE_VALUE_REJECTED")
        if not self.backend_owned or not self.read_only or not self.safe_refs_only:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_TRUTH_POSTURE_DRIFT")
        if len(self.provider_adapters) < 2 or not self.router_traces:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_INCOMPLETE_WIRING")
        if self.delegated_runtime_model_catalog.uaa_may_invoke_any_listed_model:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_DELEGATED_CATALOG_DRIFT")
        if self.model_slot_posture.hidden_model_routing_enabled:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_MODEL_SLOT_ROUTING_DRIFT")
        if self.model_slot_posture.live_auxiliary_calls_enabled:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_MODEL_SLOT_AUTHORITY_DRIFT")
        if self.role_provider_evidence.provider_sdk_call_enabled:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_ROLE_EVIDENCE_AUTHORITY_DRIFT")
        if self.role_provider_evidence.model_invocation_performed:
            raise ValueError("MODEL_PROVIDER_CONTROL_PLANE_ROLE_EVIDENCE_MODEL_CALL_DRIFT")
        return self


def build_model_provider_control_plane_read_model(
    *,
    env: Mapping[str, str] | None = None,
    credential_readiness: ProviderCredentialReadinessSummary | None = None,
    provider_catalog: ProviderCatalog | None = None,
) -> ModelProviderControlPlaneReadModel:
    readiness = credential_readiness or build_provider_credential_readiness_summary()
    catalog = provider_catalog or build_provider_setup_guide_catalog()
    inventory = inspect_local_model_inventory()
    gateway_readiness = inspect_local_model_gateway(env=env)
    runtime_profiles = build_runtime_profile_isolation_read_model()
    provider_model_refs = [
        TINY_PROVIDER_INVOCATION_MODEL_REF,
        SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        *[provider.cost_governor_binding.model_ref for provider in readiness.providers],
    ]
    router_trace = _build_model_router_trace(readiness)
    return ModelProviderControlPlaneReadModel(
        authority=ModelProviderAuthoritySummary(),
        provider_adapters=[
            ProviderAdapterRuntimePosture(
                adapter_ref=TINY_LIVE_PROVIDER_ADAPTER_REF,
                provider_ref=TINY_PROVIDER_INVOCATION_PROVIDER_REF,
                model_ref=TINY_PROVIDER_INVOCATION_MODEL_REF,
                model_name_ref=TINY_LIVE_PROVIDER_MODEL_NAME_REF,
                policy_ref=TINY_PROVIDER_INVOCATION_POLICY_REF,
                endpoint_ref=TINY_LIVE_PROVIDER_ENDPOINT_REF,
                transport_ref=TINY_LIVE_PROVIDER_TRANSPORT_REF,
            ),
            ProviderAdapterRuntimePosture(
                adapter_ref=SECOND_TINY_LIVE_PROVIDER_ADAPTER_REF,
                provider_ref=SECOND_TINY_PROVIDER_INVOCATION_PROVIDER_REF,
                model_ref=SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
                model_name_ref=SECOND_TINY_LIVE_PROVIDER_MODEL_NAME_REF,
                policy_ref=SECOND_TINY_PROVIDER_INVOCATION_POLICY_REF,
                endpoint_ref=SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF,
                transport_ref=SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
            ),
        ],
        secret_status=ProviderSecretStatusPosture(
            vault_adapter_status=readiness.vault_adapter_readiness.readiness_status,
            validation_readiness_status=readiness.validation_readiness.readiness_status,
            enrollment_status=readiness.enrollment_readiness.readiness_status,
            credential_ref_statuses={
                provider.provider_id: provider.credential_ref_status
                for provider in readiness.providers
            },
        ),
        network_allowlists=ProviderNetworkAllowlistPosture(
            allowlist_refs=[
                "provider-network-allowlist-ref:tiny-exact-approved:v1",
                PROVIDER_CREDENTIAL_VALIDATION_NETWORK_SCOPE_REF,
            ],
            endpoint_refs=[
                TINY_LIVE_PROVIDER_ENDPOINT_REF,
                SECOND_TINY_LIVE_PROVIDER_ENDPOINT_REF,
                PROVIDER_CREDENTIAL_VALIDATION_ENDPOINT_REF,
            ],
            transport_refs=[
                TINY_LIVE_PROVIDER_TRANSPORT_REF,
                SECOND_TINY_LIVE_PROVIDER_TRANSPORT_REF,
                "provider-credential-validation-transport-ref:openai-compatible-models",
            ],
        ),
        model_metadata_discovery=ModelMetadataDiscoveryPosture(
            provider_catalog_ref=catalog.catalog_ref,
            provider_count=len(catalog.provider_cards),
            provider_model_refs=provider_model_refs,
            local_inventory_status=inventory.status,
            local_inventory_model_ref_count=len(inventory.models),
            local_gateway_model_ref=f"model-ref:local:{DEFAULT_UAA_LLAMA_CPP_MODEL_ID}",
        ),
        cost_hooks=ProviderCostHookPosture(
            cost_governor_posture_ref=readiness.cost_governor_posture_ref,
            cost_governor_decision_ref=readiness.cost_governor_decision_ref,
        ),
        local_llama_cpp_lifecycle=LocalLlamaCppLifecyclePosture(
            gateway_readiness=gateway_readiness,
        ),
        router_traces=[router_trace],
        delegated_runtime_model_catalog=_build_delegated_runtime_model_catalog(
            provider_catalog_ref=catalog.catalog_ref,
            runtime_profile_count=runtime_profiles.profile_count,
        ),
        model_slot_posture=_build_model_slot_posture(),
        role_provider_evidence=build_role_based_model_provider_evidence(
            provider_readiness_items=readiness.providers,
            provider_catalog_ref=catalog.catalog_ref,
            router_trace_refs=[router_trace.trace_ref],
        ),
        model_provider_research_posture=_build_model_provider_research_posture(
            readiness=readiness,
            provider_catalog=catalog,
        ),
        provider_catalog_ref=catalog.catalog_ref,
    )


def _build_delegated_runtime_model_catalog(
    *,
    provider_catalog_ref: str,
    runtime_profile_count: int,
) -> DelegatedRuntimeModelCatalogPosture:
    records = [
        DelegatedRuntimeModelAvailabilityRecord(
            runtime_ref="runtime-ref:hermes:delegated-coding",
            runtime_profile_ref="runtime-profile-ref:uaa:coding",
            delegated_runtime_profile_ref="delegated-profile-ref:hermes:coding",
            provider_ref="provider-ref:delegated-runtime:hermes",
            model_ref="model-ref:delegated-runtime:hermes:coding-primary",
            display_label="Hermes coding primary model ref",
            runtime_availability_status="runtime_reports_available",
            uaa_invocation_posture="blocked_no_exact_invocation_lane",
            cost_metadata_status="cost_unknown_blocks_use",
            latency_metadata_status="latency_unknown_blocks_use",
            source_ref="runtime-capability-ref:hermes:coding:model-catalog",
            cost_posture_ref="cost-posture-ref:delegated-runtime:unknown-paid-cost",
            latency_posture_ref="latency-posture-ref:delegated-runtime:not-measured",
            runtime_reported_available=True,
            safe_summary=(
                "Hermes coding profile reports a model ref, but UAA has not "
                "authorized invocation from this catalog."
            ),
            blocked_authority_refs=[
                "blocked-state:model-provider:runtime-availability-is-not-invocation",
                "blocked-state:model-provider:delegated-runtime-invocation",
                "blocked-state:model-provider:cost-unknown",
            ],
        ),
        DelegatedRuntimeModelAvailabilityRecord(
            runtime_ref="runtime-ref:hermes:delegated-review",
            runtime_profile_ref="runtime-profile-ref:uaa:review",
            delegated_runtime_profile_ref="delegated-profile-ref:hermes:review",
            provider_ref="provider-ref:delegated-runtime:hermes",
            model_ref="model-ref:delegated-runtime:hermes:review-primary",
            display_label="Hermes review primary model ref",
            runtime_availability_status="runtime_reports_available",
            uaa_invocation_posture="blocked_no_exact_invocation_lane",
            cost_metadata_status="cost_unknown_blocks_use",
            latency_metadata_status="latency_unknown_blocks_use",
            source_ref="runtime-capability-ref:hermes:review:model-catalog",
            cost_posture_ref="cost-posture-ref:delegated-runtime:unknown-paid-cost",
            latency_posture_ref="latency-posture-ref:delegated-runtime:not-measured",
            runtime_reported_available=True,
            safe_summary=(
                "Hermes review profile reports a model ref, but UAA treats it "
                "as proposal metadata until an exact invocation lane exists."
            ),
            blocked_authority_refs=[
                "blocked-state:model-provider:runtime-availability-is-not-invocation",
                "blocked-state:model-provider:delegated-runtime-invocation",
                "blocked-state:model-provider:cost-unknown",
            ],
        ),
        DelegatedRuntimeModelAvailabilityRecord(
            runtime_ref="runtime-ref:uaa-native:local-llama-cpp",
            runtime_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:local-llama-cpp",
            provider_ref="provider-ref:uaa-native:local-runtime",
            model_ref=f"model-ref:local:{DEFAULT_UAA_LLAMA_CPP_MODEL_ID}",
            display_label="UAA local llama.cpp model ref",
            runtime_availability_status="local_gateway_metadata_available",
            uaa_invocation_posture="metadata_only_existing_lane_separate",
            cost_metadata_status="local_hardware_cost_posture_only",
            latency_metadata_status="local_gateway_readiness_only",
            source_ref="local-model-inventory-ref:llama-cpp:metadata",
            cost_posture_ref="cost-posture-ref:local-runtime:hardware-only",
            latency_posture_ref="latency-posture-ref:local-gateway:readiness-only",
            runtime_reported_available=True,
            safe_summary=(
                "Local llama.cpp metadata is visible here, while any existing "
                "exact local invocation lane remains separate from catalog visibility."
            ),
            blocked_authority_refs=[
                "blocked-state:model-provider:catalog-visibility-is-not-invocation",
                "blocked-state:model-provider:lifecycle-start-from-catalog",
                "blocked-state:model-provider:model-output-as-authority",
            ],
        ),
        DelegatedRuntimeModelAvailabilityRecord(
            runtime_ref="runtime-ref:hermes:delegated-research",
            runtime_profile_ref="runtime-profile-ref:uaa:research",
            delegated_runtime_profile_ref="delegated-profile-ref:hermes:research",
            provider_ref="provider-ref:delegated-runtime:hermes",
            model_ref="model-ref:delegated-runtime:hermes:research-planned",
            display_label="Hermes research planned model ref",
            runtime_availability_status="runtime_reports_planned",
            uaa_invocation_posture="blocked_profile_not_configured",
            cost_metadata_status="cost_unknown_blocks_use",
            latency_metadata_status="latency_unknown_blocks_use",
            source_ref="runtime-capability-ref:hermes:research:model-catalog",
            cost_posture_ref="cost-posture-ref:delegated-runtime:unknown-paid-cost",
            latency_posture_ref="latency-posture-ref:delegated-runtime:not-measured",
            runtime_reported_available=False,
            safe_summary=(
                "Hermes research profile is planned and remains blocked for "
                "UAA model invocation."
            ),
            blocked_authority_refs=[
                "blocked-state:model-provider:runtime-profile-not-configured",
                "blocked-state:model-provider:delegated-runtime-invocation",
                "blocked-state:web-access:live-fetch-by-control-plane",
            ],
        ),
    ]
    return DelegatedRuntimeModelCatalogPosture(
        provider_catalog_ref=provider_catalog_ref,
        model_count=len(records),
        runtime_profile_count=runtime_profile_count,
        runtime_reported_available_count=len(
            [record for record in records if record.runtime_reported_available]
        ),
        records=records,
    )


def _build_model_slot_posture() -> ModelSlotPostureReadModel:
    shared_blockers = [
        "blocked-state:model-slot:live-auxiliary-model-calls",
        "blocked-state:model-slot:provider-sdk-use",
        "blocked-state:model-slot:hidden-model-routing",
    ]
    records = [
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:main-thinking",
            slot_role="main_thinking",
            display_label="Main thinking",
            intended_provider_ref="provider-ref:uaa-governed:main",
            intended_model_ref="model-ref:uaa:intended-main-thinking",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:main",
            configured_status="configured_metadata_only",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:main-cost-policy-required",
            latency_posture_ref="latency-posture-ref:model-slot:main-not-measured",
            route_decision_trace_ref="model-route-trace-ref:model-slot:main-thinking",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            warning_refs=["warning-ref:model-slot:main-thinking-cost-policy-required"],
            safe_summary=(
                "Main reasoning slot is visible as intended routing metadata only; "
                "UAA does not call or switch a model from this posture."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-slot:runtime-selection-mutation",
            ],
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:summarization",
            slot_role="summarization",
            display_label="Summarization",
            intended_provider_ref="provider-ref:uaa-governed:auxiliary",
            intended_model_ref="model-ref:uaa:intended-summarization-small",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:summarization",
            configured_status="configured_metadata_only",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:cheap-model-required",
            latency_posture_ref="latency-posture-ref:model-slot:fast-path-required",
            route_decision_trace_ref="model-route-trace-ref:model-slot:summarization",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            safe_summary=(
                "Summarization slot is intended to use a cheap/fast model later, "
                "but no auxiliary call is enabled by this read model."
            ),
            blocked_authority_refs=shared_blockers,
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:title",
            slot_role="title",
            display_label="Title generation",
            intended_provider_ref="provider-ref:uaa-governed:auxiliary",
            intended_model_ref="model-ref:uaa:intended-title-small",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:title",
            configured_status="configured_metadata_only",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:cheap-model-required",
            latency_posture_ref="latency-posture-ref:model-slot:fast-path-required",
            route_decision_trace_ref="model-route-trace-ref:model-slot:title",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            safe_summary=(
                "Title slot is visible for future cheap auxiliary routing; it "
                "does not create hidden title model calls."
            ),
            blocked_authority_refs=shared_blockers,
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:approval-scoring",
            slot_role="approval_scoring",
            display_label="Approval scoring",
            intended_provider_ref="provider-ref:uaa-governed:policy",
            intended_model_ref="model-ref:uaa:intended-approval-scoring",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:approval",
            configured_status="planned_not_configured",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:approval-cost-review",
            latency_posture_ref="latency-posture-ref:model-slot:policy-not-measured",
            route_decision_trace_ref="model-route-trace-ref:model-slot:approval-scoring",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            warning_refs=["warning-ref:model-slot:approval-scoring-no-hidden-routing"],
            safe_summary=(
                "Approval scoring remains planned metadata; approval decisions "
                "are not delegated to a hidden model."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-slot:approval-decision-by-model",
            ],
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:compression",
            slot_role="compression",
            display_label="Context compression",
            intended_provider_ref="provider-ref:uaa-governed:auxiliary",
            intended_model_ref="model-ref:uaa:intended-compression-small",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:compression",
            configured_status="planned_not_configured",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:cheap-model-required",
            latency_posture_ref="latency-posture-ref:model-slot:fast-path-required",
            route_decision_trace_ref="model-route-trace-ref:model-slot:compression",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            safe_summary=(
                "Compression slot is a future auxiliary intent and does not "
                "persist operator input or context bodies."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-slot:raw-prompt-persistence",
            ],
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:retrieval",
            slot_role="retrieval",
            display_label="Retrieval helper",
            intended_provider_ref="provider-ref:uaa-native:retrieval",
            intended_model_ref="model-ref:uaa:intended-retrieval-local-metadata",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:uaa-native:retrieval",
            configured_status="configured_metadata_only",
            uaa_execution_posture="metadata_only_existing_lane_separate",
            provider_readiness_ref="memory-context-pack-posture-ref:reviewed-refs-only",
            cost_posture_ref="cost-posture-ref:model-slot:local-metadata-only",
            latency_posture_ref="latency-posture-ref:model-slot:local-readiness-only",
            route_decision_trace_ref="model-route-trace-ref:model-slot:retrieval",
            model_output_truth_ref="truth-boundary-ref:retrieval-output:not-authority",
            safe_summary=(
                "Retrieval slot points at reviewed local metadata and context refs; "
                "it does not inject hidden context or call a retrieval model."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-slot:hidden-context-injection",
            ],
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:vision",
            slot_role="vision",
            display_label="Vision",
            intended_provider_ref="provider-ref:uaa-governed:vision",
            intended_model_ref="model-ref:uaa:intended-vision-planned",
            source_profile_ref="runtime-profile-ref:uaa:sealed-default",
            delegated_runtime_profile_ref="delegated-profile-ref:hermes:vision-planned",
            configured_status="planned_not_configured",
            uaa_execution_posture="blocked_missing_runtime_profile",
            provider_readiness_ref=(
                "control-center-dashboard-field:provider_credential_readiness"
            ),
            cost_posture_ref="cost-posture-ref:model-slot:vision-cost-unknown",
            latency_posture_ref="latency-posture-ref:model-slot:vision-not-measured",
            route_decision_trace_ref="model-route-trace-ref:model-slot:vision",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            warning_refs=["warning-ref:model-slot:vision-unavailable"],
            safe_summary=(
                "Vision slot is planned and unavailable; no image/model provider "
                "call is enabled."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-slot:vision-provider-not-configured",
            ],
        ),
        ModelSlotPostureRecord(
            slot_ref="model-slot-ref:uaa:review",
            slot_role="review",
            display_label="Review",
            intended_provider_ref="provider-ref:delegated-runtime:hermes",
            intended_model_ref="model-ref:delegated-runtime:hermes:review-primary",
            source_profile_ref="runtime-profile-ref:uaa:review",
            delegated_runtime_profile_ref="delegated-profile-ref:hermes:review",
            configured_status="runtime_reported_available_not_authorized",
            uaa_execution_posture="blocked_no_exact_model_authority",
            provider_readiness_ref=DELEGATED_RUNTIME_MODEL_CATALOG_CONTRACT_REF,
            cost_posture_ref="cost-posture-ref:delegated-runtime:unknown-paid-cost",
            latency_posture_ref="latency-posture-ref:delegated-runtime:not-measured",
            route_decision_trace_ref="model-route-trace-ref:model-slot:review",
            model_output_truth_ref="truth-boundary-ref:model-output:not-authority",
            warning_refs=[
                "warning-ref:model-slot:review-runtime-availability-not-authority"
            ],
            safe_summary=(
                "Review slot can reference Hermes review availability metadata, "
                "but UAA cannot invoke it from this posture."
            ),
            blocked_authority_refs=[
                *shared_blockers,
                "blocked-state:model-provider:runtime-availability-is-not-invocation",
            ],
        ),
    ]
    return ModelSlotPostureReadModel(
        slot_count=len(records),
        warning_count=sum(bool(record.warning_refs) for record in records),
        records=records,
        auxiliary_slot_refs=[
            record.slot_ref
            for record in records
            if record.slot_ref != "model-slot-ref:uaa:main-thinking"
        ],
    )


def _build_model_provider_research_posture(
    *,
    readiness: ProviderCredentialReadinessSummary,
    provider_catalog: ProviderCatalog,
) -> ModelProviderResearchPosture:
    web_runtime_contract = build_web_runtime_authority_contract()
    provider_postures = [
        _provider_research_posture(provider) for provider in readiness.providers
    ]
    if not provider_postures:
        provider_postures = [
            ModelProviderResearchProviderPosture(
                provider_id="provider:catalog:fallback",
                provider_label="Provider catalog fallback",
                provider_kind="metadata_only",
                local_remote_posture="remote_provider_reference",
                status="reference_only",
                credential_readiness_status="reference_missing",
                blocked_reason_ref="blocked-state:model-provider:no-provider-readiness-items",
                last_safe_diagnostic_receipt_ref=(
                    "receipt-ref:model-provider-research:fallback-diagnostic"
                ),
                operator_next_step=(
                    "Inspect provider setup guide and credential readiness before "
                    "considering any exact provider lane."
                ),
            )
        ]
    return ModelProviderResearchPosture(
        provider_count=len(provider_postures),
        provider_postures=provider_postures,
        external_information=ExternalInformationResearchPosture(
            web_runtime_authority_contract_ref=web_runtime_contract.contract_ref,
        ),
        docs_refs=[
            "docs/control_center/UAA_GOATCITADEL_CATCHUP_MODEL_PROVIDER_RESEARCH.md",
            "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
            "docs/network/WEB_ACCESS_GATEWAY.md",
            "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
        ],
        blocked_authority_refs=[
            "blocked-state:model-provider:provider-sdk-calls",
            "blocked-state:model-provider:remote-model-calls-by-control-plane",
            "blocked-state:model-provider:model-output-as-authority",
            "blocked-state:model-provider:credential-material-display",
            "blocked-state:web-access:live-fetch-by-control-plane",
            "blocked-state:web-access:browser-automation",
            "blocked-state:web-access:provider-search-calls",
            "blocked-state:model-provider:memory-action-context-escalation",
            "blocked-state:model-provider:production-authority",
            *provider_catalog.blocked_authorities[:3],
        ],
    )


def _provider_research_posture(
    provider: Any,
) -> ModelProviderResearchProviderPosture:
    status: Literal[
        "reference_only",
        "blocked_missing_refs",
        "approval_required_exact_lane",
    ] = (
        "approval_required_exact_lane"
        if provider.provider_model_refs_bound and provider.credential_configured
        else "blocked_missing_refs"
    )
    return ModelProviderResearchProviderPosture(
        provider_id=provider.provider_id,
        provider_label=provider.provider_label,
        provider_kind=provider.provider_kind,
        local_remote_posture="remote_provider_reference",
        status=status,
        credential_readiness_status=provider.credential_ref_status,
        cost_latency_metadata_status="static_cost_metadata_only",
        supported_authority_mode=(
            "exact_lane_requires_approval"
            if status == "approval_required_exact_lane"
            else "guidance_only"
        ),
        blocked_reason_ref=(
            provider.blocker_codes[0]
            if provider.blocker_codes
            else "blocked-state:model-provider:metadata-only"
        ),
        last_safe_diagnostic_receipt_ref=(
            f"receipt-ref:model-provider-research:{provider.provider_id.replace(':', '-')}:diagnostic"
        ),
        operator_next_step=(
            "Bind provider, model, credential, CostGovernor, approval, "
            "idempotency, and receipt refs before any future exact live lane."
        ),
    )


def _build_model_router_trace(
    readiness: ProviderCredentialReadinessSummary,
) -> ModelRouterTracePosture:
    request = ModelRouteRequest(
        request_id="model-provider-control-plane-route-preview",
        run_id="run-ref:model-provider-control-plane:preview",
        actor_context=ActorContext(
            actor_type=ActorType.orchestrator,
            actor_id="model-provider-control-plane",
            authority_source=AuthoritySource.system_policy,
        ),
        task_class="model_provider_control_plane_trace",
        prompt_summary="Safe route preview metadata only.",
        data_classification=DataClassification(
            classification=ClassificationValue.project_private,
            source="model-provider-control-plane",
        ),
        required_capabilities=[ModelTaskCapability.chat],
        estimated_input_tokens=600,
        estimated_output_tokens=200,
        routing_policy=ModelRoutingPolicy(
            policy_id="policy:model-provider-control-plane:local-first",
            required_capabilities=[ModelTaskCapability.chat],
            prefer_local=True,
            allow_cloud=False,
            allow_paid=False,
            reason_codes_required=True,
        ),
        available_profiles=[
            ModelCapabilityProfile(
                model_profile_id="model-profile-ref:local-llama-cpp:chat",
                provider_kind=ModelProviderKind.local_runtime,
                runtime_id="runtime-ref:local-llama-cpp:m164",
                model_id=DEFAULT_UAA_LLAMA_CPP_MODEL_ID,
                display_name="Local llama.cpp chat",
                capabilities=[
                    ModelTaskCapability.chat,
                    ModelTaskCapability.summarization,
                ],
                privacy_class=ModelPrivacyClass.local_only,
                max_context_tokens=8192,
                supports_streaming=False,
                supports_tools=False,
                supports_structured_output=False,
                cost_per_1k_input_tokens=None,
                cost_per_1k_output_tokens=None,
                time_to_first_token_ms=150,
                enabled=True,
                owner="ultimate-ai-agent",
                source="m164-local-gateway-contract",
                version="m164",
            ),
            ModelCapabilityProfile(
                model_profile_id="model-profile-ref:cloud-provider:blocked",
                provider_kind=ModelProviderKind.cloud_provider,
                provider_id=PROVIDER_CREDENTIAL_VALIDATION_PROVIDER_REF,
                model_id="model-ref:cloud-provider:not-selected",
                display_name="Cloud provider blocked preview",
                capabilities=[ModelTaskCapability.chat, ModelTaskCapability.reasoning],
                privacy_class=ModelPrivacyClass.cloud_allowed,
                max_context_tokens=32768,
                cost_per_1k_input_tokens=0.01,
                cost_per_1k_output_tokens=0.03,
                credential_ref="credential-ref:cloud-provider:not-configured",
                enabled=True,
                owner="ultimate-ai-agent",
                source="provider-control-plane-blocked-preview",
                version="v1",
            ),
        ],
        credential_availability={"credential-ref:cloud-provider:not-configured": False},
        consent_refs=[],
        event_ref="model-router-trace-ref:model-provider-control-plane:preview",
    )
    decision = ModelRouter().route(request)
    router_dry_run = readiness.router_dry_run_readiness
    return ModelRouterTracePosture(
        trace_ref="model-router-trace-ref:model-provider-control-plane:preview",
        decision=decision,
        provider_router_trace_ref=router_dry_run.router_run_ref,
        provider_router_status=router_dry_run.status,
        selected_profile_ref=decision.selected_profile_id,
        selected_model_ref=decision.selected_model_id,
        candidate_profile_refs=decision.candidate_profile_ids,
        rejected_profile_refs=decision.rejected_profile_ids,
        reason_codes=decision.reason_codes,
    )
