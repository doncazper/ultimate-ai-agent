from typing import Any
from tests.m7_helpers import actor, classification, local_profile, policy, route_request
from ultimate_ai_agent.core.model_router import ModelRouter
from ultimate_ai_agent.core.model_runtime import (
    ModelRuntimeAdapterManifest,
    ModelRuntimeKind,
    ModelRuntimeOutputFormat,
    ModelRuntimeRequest,
    ModelRuntimeSafetyMode,
)


def simulated_manifest(enabled: bool = True, max_input_tokens: int = 4096) -> ModelRuntimeAdapterManifest:
    return ModelRuntimeAdapterManifest(
        adapter_id="sim_adapter",
        runtime_kind=ModelRuntimeKind.simulated,
        display_name="Simulated Runtime Adapter",
        description="Deterministic simulated adapter for M8 tests.",
        supported_provider_kinds=["local_runtime"],
        supported_capabilities=["chat", "coding"],
        safety_mode=ModelRuntimeSafetyMode.simulated,
        accepts_model_profile_ids=["local_coder"],
        requires_credential_ref=False,
        allowed_credential_refs=[],
        supports_streaming=False,
        supports_tools=False,
        supports_json_mode=True,
        supports_structured_output=True,
        max_context_tokens=8192,
        max_input_tokens=max_input_tokens,
        max_output_tokens=2048,
        owner="tests",
        source="fixture",
        version="0.0.0",
        enabled=enabled,
    )


def runtime_request(**overrides: Any) -> ModelRuntimeRequest:
    payload = {
        "runtime_request_id": "mrt_req_1",
        "run_id": "run_m8",
        "route_decision_ref": "mroute_decision",
        "model_profile_id": "local_coder",
        "model_id": "local_coder_model",
        "adapter_id": "sim_adapter",
        "actor_context": actor(),
        "prompt_summary": "Summarize referenced context without exposing raw prompt text.",
        "input_refs": ["context_pack:cp_1", "memory:mem_1"],
        "output_format": ModelRuntimeOutputFormat.text,
        "estimated_input_tokens": 512,
        "max_output_tokens": 256,
        "safety_mode": ModelRuntimeSafetyMode.simulated,
        "data_classification": classification(),
        "consent_refs": ["consent_m8"],
        "approval_ref": None,
        "secret_handle_refs": ["secret_handle_ref"],
        "event_ref": "evt_route_selected",
        "trace_id": "trace_m8",
        "metadata": {"policy_warnings": []},
    }
    payload.update(overrides)
    return ModelRuntimeRequest(**payload)


def selected_route_pair() -> tuple[Any, ...]:
    profile = local_profile()
    request = route_request(profiles=[profile], routing_policy=policy(prefer_local=True, allow_cloud=False, allow_paid=False))
    decision = ModelRouter().route(request)
    return request, decision
