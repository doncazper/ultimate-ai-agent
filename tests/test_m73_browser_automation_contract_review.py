from typing import Any
import pytest

from ultimate_ai_agent.core.browser import (
    BrowserAutomationCapabilityKind,
    BrowserAutomationContractReviewPolicy,
    BrowserAutomationContractReviewRequest,
    BrowserAutomationContractReviewStatus,
    build_browser_automation_contract_review_decision,
    validate_browser_automation_contract_review_policy,
    validate_browser_automation_contract_review_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "review_ref": "browser-contract-review:m73",
        "candidate_ref": "browser-contract-candidate:m73-observe-only-adapter",
        "actor_ref": "actor:local-reviewer",
        "proposed_adapter_ref": "browser-adapter:m74-observe-only-candidate",
        "safe_name": "Browser observe-only adapter contract review",
        "capability_kind": BrowserAutomationCapabilityKind.observe_only_adapter,
        "safe_summary": "Review the future M74 observe-only browser adapter contract without enabling browser automation.",
        "safe_browser_policy_ref": "browser-policy:m74-future-observe-only",
        "risk_ref": "risk:browser-review-only",
    }
    data.update(overrides)
    return BrowserAutomationContractReviewRequest(**data)


def test_browser_automation_contract_review_is_contract_only_and_no_authority() -> None:
    decision = build_browser_automation_contract_review_decision(_request())

    assert decision.status == BrowserAutomationContractReviewStatus.review_ready
    assert decision.review_allowed is True
    assert decision.contract_only is True
    assert decision.review_only is True
    assert decision.disabled_by_default is True
    assert decision.deterministic is True
    assert decision.m74_candidate_only is True
    assert decision.future_milestone_required is True
    assert decision.browser_automation_allowed is False
    assert decision.browser_observe_allowed is False
    assert decision.browser_navigation_allowed is False
    assert decision.browser_click_allowed is False
    assert decision.form_fill_allowed is False
    assert decision.screenshot_allowed is False
    assert decision.dom_read_allowed is False
    assert decision.network_call_allowed is False
    assert decision.tool_execution_allowed is False
    assert decision.backend_route_allowed is False
    assert decision.control_center_control_allowed is False
    assert decision.production_authority_granted is False
    assert decision.receipt_plan.browser_automation_performed is False
    assert decision.receipt_plan.raw_dom_stored is False
    assert decision.receipt_plan.screenshot_stored is False
    assert decision.receipt_plan.side_effects_performed == []
    assert "M73_BROWSER_AUTOMATION_CONTRACT_REVIEW_ONLY" in decision.reason_codes
    assert "M74_REMAINS_FUTURE" in decision.reason_codes


@pytest.mark.parametrize(
    "capability_kind",
    [
        BrowserAutomationCapabilityKind.navigation,
        BrowserAutomationCapabilityKind.click,
        BrowserAutomationCapabilityKind.form_fill,
        BrowserAutomationCapabilityKind.screenshot_capture,
        BrowserAutomationCapabilityKind.dom_read,
        BrowserAutomationCapabilityKind.download_or_upload,
        BrowserAutomationCapabilityKind.authenticated_profile_access,
        BrowserAutomationCapabilityKind.remote_browser_control,
        BrowserAutomationCapabilityKind.browser_network_interception,
    ],
)
def test_effectful_browser_capabilities_are_future_review_only(
    capability_kind: BrowserAutomationCapabilityKind,
) -> None:
    decision = build_browser_automation_contract_review_decision(
        _request(
            candidate_ref=f"browser-contract-candidate:m73-{capability_kind.value}",
            capability_kind=capability_kind,
            safe_name=f"Future {capability_kind.value} browser contract review",
        )
    )

    assert decision.status == BrowserAutomationContractReviewStatus.future_milestone
    assert decision.review_allowed is True
    assert decision.browser_automation_allowed is False
    assert decision.browser_click_allowed is False
    assert decision.form_fill_allowed is False
    assert decision.future_milestone_required is True
    assert "FUTURE_BROWSER_MILESTONE_REQUIRED" in decision.reason_codes


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("browser_automation_requested", "BROWSER_AUTOMATION_DENIED"),
        ("browser_observe_requested", "BROWSER_OBSERVE_DENIED"),
        ("browser_navigation_requested", "BROWSER_NAVIGATION_DENIED"),
        ("browser_click_requested", "BROWSER_CLICK_DENIED"),
        ("form_fill_requested", "FORM_FILL_DENIED"),
        ("screenshot_requested", "SCREENSHOT_DENIED"),
        ("dom_read_requested", "DOM_READ_DENIED"),
        ("authenticated_profile_requested", "AUTHENTICATED_PROFILE_DENIED"),
        ("download_or_upload_requested", "DOWNLOAD_OR_UPLOAD_DENIED"),
        ("remote_browser_requested", "REMOTE_BROWSER_DENIED"),
        ("network_interception_requested", "NETWORK_INTERCEPTION_DENIED"),
        ("network_call_requested", "NETWORK_CALL_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_browser_contract_review_denies_authority_request_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_browser_automation_contract_review_request(_request(**{field: True}))


def test_browser_contract_review_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "browser_click_requested": True,
            "contains_raw_dom": True,
            "contains_screenshot_bytes": True,
        }
    )

    with pytest.raises(ValueError, match="BROWSER_CLICK_DENIED"):
        build_browser_automation_contract_review_decision(request)


def test_approval_refs_cannot_authorize_browser_review() -> None:
    with pytest.raises(ValueError, match="APPROVAL_REF_NOT_AUTHORITY"):
        build_browser_automation_contract_review_decision(_request(approval_ref="approval:m73"))

    with pytest.raises(ValueError, match="APPROVAL_TEST_REF_DENIED"):
        build_browser_automation_contract_review_decision(
            _request(approval_test_ref="approval_test_m73")
        )

    with pytest.raises(ValueError, match="AUTHORITY_REF_NOT_BROWSER_AUTHORITY"):
        build_browser_automation_contract_review_decision(
            _request(authority_refs=["context-pack:m73"])
        )


def test_browser_contract_review_denies_raw_or_secret_like_content() -> None:
    with pytest.raises(ValueError, match="RAW_DOM_DENIED"):
        build_browser_automation_contract_review_decision(_request(contains_raw_dom=True))

    with pytest.raises(ValueError, match="SCREENSHOT_BYTES_DENIED"):
        build_browser_automation_contract_review_decision(
            _request(contains_screenshot_bytes=True)
        )

    with pytest.raises(ValueError, match="SECRET_LIKE_BROWSER_CONTENT_DENIED"):
        build_browser_automation_contract_review_decision(
            _request(metadata={"session_cookie": "secret-value"})
        )


def test_browser_contract_review_unknown_capability_is_denied() -> None:
    decision = build_browser_automation_contract_review_decision(
        _request(capability_kind=BrowserAutomationCapabilityKind.unknown)
    )

    assert decision.status == BrowserAutomationContractReviewStatus.denied
    assert decision.review_allowed is False
    assert decision.browser_automation_allowed is False
    assert "UNKNOWN_BROWSER_CAPABILITY_DENIED" in decision.reason_codes


def test_browser_contract_review_policy_denies_enablement() -> None:
    policy = BrowserAutomationContractReviewPolicy(
        browser_automation_enabled=True,
        browser_click_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="BROWSER_AUTOMATION_DENIED"):
        validate_browser_automation_contract_review_policy(policy)
