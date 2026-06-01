from tests.m7_helpers import classification, cloud_profile, local_profile, policy, route_request
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue
from ultimate_ai_agent.core.model_router import ModelPrivacyClass, ModelRouteStatus, ModelRouter


def test_cloud_candidate_blocked_in_local_only_privacy_mode():
    request = route_request(
        profiles=[cloud_profile()],
        routing_policy=policy(privacy_mode=ModelPrivacyClass.local_only, allow_cloud=False),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.privacy_blocked
    assert decision.selected_profile_id is None
    assert "CLOUD_BLOCKED_BY_PRIVACY_MODE" in decision.reason_codes


def test_sensitive_personal_cloud_route_requires_approval_when_policy_demands_it():
    request = route_request(
        profiles=[cloud_profile()],
        data_classification=classification(ClassificationValue.sensitive_personal),
        routing_policy=policy(require_human_approval_for_cloud=True, allow_cloud=True),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.approval_required
    assert decision.required_approval is True
    assert "CLOUD_APPROVAL_REQUIRED" in decision.reason_codes


def test_credential_secret_never_routes_to_model():
    request = route_request(
        profiles=[local_profile(), cloud_profile()],
        data_classification=classification(ClassificationValue.credential_secret),
    )

    decision = ModelRouter().route(request)

    assert decision.status == ModelRouteStatus.privacy_blocked
    assert decision.selected_profile_id is None
    assert "CREDENTIAL_SECRET_NEVER_TO_MODEL" in decision.reason_codes
