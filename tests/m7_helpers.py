from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.model_router import (
    ModelCapabilityProfile,
    ModelPrivacyClass,
    ModelProviderKind,
    ModelRouteRequest,
    ModelRoutingPolicy,
    ModelTaskCapability,
)


def actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.orchestrator,
        actor_id="test_orchestrator",
        authority_source=AuthoritySource.explicit_user_request,
    )


def classification(value: ClassificationValue = ClassificationValue.project_private) -> DataClassification:
    return DataClassification(classification=value, source="test")


def local_profile(
    profile_id: str = "local_coder",
    *,
    capabilities: list[ModelTaskCapability] | None = None,
    max_context_tokens: int = 8192,
    enabled: bool = True,
) -> ModelCapabilityProfile:
    return ModelCapabilityProfile(
        model_profile_id=profile_id,
        provider_kind=ModelProviderKind.local_runtime,
        runtime_id="rt_local",
        model_id=f"{profile_id}_model",
        display_name="Local Coding Model",
        capabilities=capabilities or [ModelTaskCapability.chat, ModelTaskCapability.coding],
        privacy_class=ModelPrivacyClass.local_only,
        max_context_tokens=max_context_tokens,
        estimated_tokens_per_second=30,
        time_to_first_token_ms=120,
        enabled=enabled,
        owner="tests",
        source="fixture",
        version="0.0.0",
    )


def cloud_profile(
    profile_id: str = "cloud_reasoner",
    *,
    capabilities: list[ModelTaskCapability] | None = None,
    cost_per_1k_input_tokens: float | None = 0.01,
    cost_per_1k_output_tokens: float | None = 0.03,
    credential_ref: str | None = None,
    enabled: bool = True,
) -> ModelCapabilityProfile:
    return ModelCapabilityProfile(
        model_profile_id=profile_id,
        provider_kind=ModelProviderKind.cloud_provider,
        provider_id="provider_cloud",
        model_id=f"{profile_id}_model",
        display_name="Cloud Reasoner",
        capabilities=capabilities or [ModelTaskCapability.chat, ModelTaskCapability.reasoning],
        privacy_class=ModelPrivacyClass.cloud_allowed,
        max_context_tokens=32768,
        cost_per_1k_input_tokens=cost_per_1k_input_tokens,
        cost_per_1k_output_tokens=cost_per_1k_output_tokens,
        time_to_first_token_ms=200,
        credential_ref=credential_ref,
        enabled=enabled,
        owner="tests",
        source="fixture",
        version="0.0.0",
    )


def policy(**overrides) -> ModelRoutingPolicy:
    payload = {
        "policy_id": "policy_test",
        "required_capabilities": [ModelTaskCapability.chat],
        "preferred_capabilities": [],
        "prefer_local": False,
        "allow_cloud": True,
        "allow_paid": True,
        "fallback_allowed": False,
        "reason_codes_required": True,
    }
    payload.update(overrides)
    return ModelRoutingPolicy(**payload)


def route_request(
    *,
    profiles: list[ModelCapabilityProfile],
    routing_policy: ModelRoutingPolicy | None = None,
    required_capabilities: list[ModelTaskCapability] | None = None,
    data_classification: DataClassification | None = None,
    context_budget: ContextBudget | None = None,
    credential_availability: dict[str, bool] | None = None,
    approval_ref: str | None = None,
) -> ModelRouteRequest:
    return ModelRouteRequest(
        request_id="route_req_1",
        run_id="run_m7",
        actor_context=actor(),
        task_class="coding",
        prompt_summary="Summarize the task without secrets.",
        data_classification=data_classification or classification(),
        required_capabilities=required_capabilities or [ModelTaskCapability.chat],
        estimated_input_tokens=1000,
        estimated_output_tokens=500,
        context_budget=context_budget,
        routing_policy=routing_policy or policy(required_capabilities=required_capabilities or [ModelTaskCapability.chat]),
        available_profiles=profiles,
        credential_availability=credential_availability or {},
        consent_refs=[],
        approval_ref=approval_ref,
    )
