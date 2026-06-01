from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.model_router.profiles import ModelCapabilityProfile
from ultimate_ai_agent.core.model_router.requests import ModelRouteRequest


def validate_model_capability_profile(profile: ModelCapabilityProfile) -> bool:
    if scan_payload_for_secrets(profile.model_dump()):
        raise ValueError("ModelCapabilityProfile contains secret-like content.")
    return True


def validate_model_route_request(request: ModelRouteRequest) -> bool:
    if scan_payload_for_secrets(request.prompt_summary):
        raise ValueError("ModelRouteRequest prompt_summary contains secret-like content.")
    return True
