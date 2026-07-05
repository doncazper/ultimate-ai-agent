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
    PROVIDER_CREDENTIAL_VALIDATION_POLICY_REF,
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
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


MODEL_PROVIDER_CONTROL_PLANE_CONTRACT_REF = (
    "contract-ref:model-provider-control-plane:v1"
)
MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF = (
    "GET /control-center/providers/runtime-control-plane"
)
MODEL_PROVIDER_CONTROL_PLANE_CLI_REF = (
    "scripts/inspect_model_provider_control_plane.py"
)
MODEL_PROVIDER_CONTROL_PLANE_VERIFIER_REF = (
    "scripts/verify_model_provider_control_plane.py"
)


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


class ModelProviderControlPlaneReadModel(BaseModel):
    schema_version: Literal["model_provider_control_plane.v1"] = (
        "model_provider_control_plane.v1"
    )
    contract_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CONTRACT_REF
    route_ref: str = MODEL_PROVIDER_CONTROL_PLANE_ROUTE_REF
    cli_ref: str = MODEL_PROVIDER_CONTROL_PLANE_CLI_REF
    status: Literal["governed_control_plane_wired"] = (
        "governed_control_plane_wired"
    )
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
            "docs/control_center/EXACT_APPROVED_PROVIDER_INVOCATION_PROMOTION_PLAN.md",
            "docs/model_management/UAA_P1_066_LOCAL_MODEL_CONTROL_CENTER_READ_ONLY_STATUS.md",
        ]
    )
    verifier_refs: list[str] = Field(
        default_factory=lambda: [MODEL_PROVIDER_CONTROL_PLANE_VERIFIER_REF]
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
    provider_model_refs = [
        TINY_PROVIDER_INVOCATION_MODEL_REF,
        SECOND_TINY_PROVIDER_INVOCATION_MODEL_REF,
        *[
            provider.cost_governor_binding.model_ref
            for provider in readiness.providers
        ],
    ]
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
        router_traces=[_build_model_router_trace(readiness)],
        provider_catalog_ref=catalog.catalog_ref,
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
                capabilities=[ModelTaskCapability.chat, ModelTaskCapability.summarization],
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
