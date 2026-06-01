from pydantic import ValidationError

from tests.m7_helpers import policy
from ultimate_ai_agent.core.model_router import ModelPrivacyClass, ModelProviderKind, ModelTaskCapability


def test_model_routing_policy_tracks_capability_privacy_and_cost_controls():
    routing_policy = policy(
        required_capabilities=[ModelTaskCapability.coding],
        preferred_capabilities=[ModelTaskCapability.structured_output],
        forbidden_provider_kinds=[ModelProviderKind.cloud_provider],
        privacy_mode=ModelPrivacyClass.local_only,
        prefer_local=True,
        allow_cloud=False,
        allow_paid=False,
        max_estimated_cost_usd=0,
        require_structured_output=True,
        require_tool_support=False,
    )

    assert routing_policy.privacy_mode == ModelPrivacyClass.local_only
    assert routing_policy.allow_cloud is False
    assert routing_policy.allow_paid is False
    assert ModelTaskCapability.coding in routing_policy.required_capabilities


def test_model_routing_policy_rejects_unknown_fields():
    payload = policy().model_dump()
    payload["surprise"] = "nope"

    try:
        type(policy())(**payload)
    except ValidationError as exc:
        assert "extra" in str(exc).lower()
    else:
        raise AssertionError("ModelRoutingPolicy accepted an unknown field")
