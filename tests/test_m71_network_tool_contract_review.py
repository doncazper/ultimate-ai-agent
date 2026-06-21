from typing import Any
import pytest

from ultimate_ai_agent.core.network import (
    NetworkToolCapabilityKind,
    NetworkToolContractReviewPolicy,
    NetworkToolContractReviewRequest,
    NetworkToolContractReviewStatus,
    build_network_tool_contract_review_decision,
    validate_network_tool_contract_review_policy,
    validate_network_tool_contract_review_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "review_ref": "network-tool-contract-review:m71",
        "candidate_ref": "network-tool-candidate:m71-read-only-http-fetch",
        "actor_ref": "actor:local-reviewer",
        "proposed_tool_ref": "tool:read-only-http-fetch-m72-candidate",
        "safe_name": "Allowlisted read-only HTTP fetch contract review",
        "capability_kind": NetworkToolCapabilityKind.allowlisted_read_only_http_fetch,
        "safe_summary": "Review the future M72 allowlisted read-only HTTP fetch contract without enabling network calls.",
        "allowed_host_policy_ref": "network-allowlist-policy:m72-future",
        "risk_ref": "risk:network-low-read-only-review",
    }
    data.update(overrides)
    return NetworkToolContractReviewRequest(**data)


def test_network_tool_contract_review_is_review_only_and_no_network_authority() -> None:
    decision = build_network_tool_contract_review_decision(_request())

    assert decision.status == NetworkToolContractReviewStatus.review_ready
    assert decision.review_allowed is True
    assert decision.contract_only is True
    assert decision.m72_candidate_only is True
    assert decision.future_milestone_required is True
    assert decision.network_call_allowed is False
    assert decision.http_fetch_allowed is False
    assert decision.tool_execution_allowed is False
    assert decision.backend_route_allowed is False
    assert decision.control_center_control_allowed is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.network_call_performed is False
    assert decision.receipt_plan.raw_response_body_stored is False
    assert decision.receipt_plan.credentials_or_cookies_used is False
    assert decision.receipt_plan.side_effects_performed == []
    assert "M71_NETWORK_TOOL_CONTRACT_REVIEW_ONLY" in decision.reason_codes
    assert "M72_REMAINS_FUTURE" in decision.reason_codes


@pytest.mark.parametrize(
    "capability_kind",
    [
        NetworkToolCapabilityKind.unrestricted_network_tool,
        NetworkToolCapabilityKind.authenticated_network_action,
        NetworkToolCapabilityKind.non_get_request,
        NetworkToolCapabilityKind.request_body_upload,
        NetworkToolCapabilityKind.download_or_export,
        NetworkToolCapabilityKind.browser_network_action,
        NetworkToolCapabilityKind.provider_model_call,
        NetworkToolCapabilityKind.webhook_or_callback,
        NetworkToolCapabilityKind.external_saas_sdk,
    ],
)
def test_effectful_network_capabilities_are_future_review_only(
    capability_kind: NetworkToolCapabilityKind,
) -> None:
    decision = build_network_tool_contract_review_decision(
        _request(
            candidate_ref=f"network-tool-candidate:m71-{capability_kind.value}",
            capability_kind=capability_kind,
            safe_name=f"Future {capability_kind.value} network review",
        )
    )

    assert decision.status == NetworkToolContractReviewStatus.future_milestone
    assert decision.review_allowed is True
    assert decision.network_call_allowed is False
    assert decision.http_fetch_allowed is False
    assert decision.tool_execution_allowed is False
    assert decision.future_milestone_required is True
    assert "FUTURE_NETWORK_MILESTONE_REQUIRED" in decision.reason_codes


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("network_call_requested", "NETWORK_CALL_DENIED"),
        ("http_fetch_requested", "HTTP_FETCH_DENIED"),
        ("unrestricted_network_requested", "UNRESTRICTED_NETWORK_DENIED"),
        ("authenticated_network_requested", "AUTHENTICATED_NETWORK_DENIED"),
        ("credentials_or_cookies_requested", "CREDENTIAL_OR_COOKIE_HANDLING_DENIED"),
        ("request_body_requested", "REQUEST_BODY_DENIED"),
        ("non_get_method_requested", "NON_GET_METHOD_DENIED"),
        ("download_or_export_requested", "DOWNLOAD_OR_EXPORT_DENIED"),
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("provider_model_call_requested", "PROVIDER_MODEL_CALL_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_network_tool_contract_review_denies_authority_request_flags(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_network_tool_contract_review_request(_request(**{field: True}))


def test_network_tool_contract_review_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "network_call_requested": True,
            "http_fetch_requested": True,
            "contains_raw_response_body": True,
        }
    )

    with pytest.raises(ValueError, match="NETWORK_CALL_DENIED"):
        build_network_tool_contract_review_decision(request)


def test_approval_ref_and_approval_test_ref_cannot_authorize_network_review() -> None:
    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        build_network_tool_contract_review_decision(_request(approval_ref="approval:m71"))

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        build_network_tool_contract_review_decision(_request(approval_test_ref="approval_test_m71"))


def test_network_tool_contract_review_unknown_capability_is_denied() -> None:
    decision = build_network_tool_contract_review_decision(
        _request(capability_kind=NetworkToolCapabilityKind.unknown)
    )

    assert decision.status == NetworkToolContractReviewStatus.denied
    assert decision.review_allowed is False
    assert decision.network_call_allowed is False
    assert "UNKNOWN_NETWORK_TOOL_CAPABILITY_DENIED" in decision.reason_codes


def test_network_tool_contract_review_denies_raw_or_secret_like_content() -> None:
    with pytest.raises(ValueError, match="RAW_RESPONSE_BODY_DENIED"):
        build_network_tool_contract_review_decision(_request(contains_raw_response_body=True))

    with pytest.raises(ValueError, match="SECRET_LIKE_NETWORK_TOOL_CONTENT_DENIED"):
        build_network_tool_contract_review_decision(_request(metadata={"api_key": "secret-value"}))


def test_network_tool_contract_review_policy_denies_enablement() -> None:
    policy = NetworkToolContractReviewPolicy(
        network_call_enabled=True,
        http_fetch_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="NETWORK_CALL_DENIED"):
        validate_network_tool_contract_review_policy(policy)
