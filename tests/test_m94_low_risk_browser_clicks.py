import pytest

from tests.test_m93_multi_tool_dry_run_promotion import _request as _m93_request
from ultimate_ai_agent.core.autonomy import build_multi_tool_dry_run_promotion_decision
from ultimate_ai_agent.core.browser import (
    LowRiskBrowserClickPolicy,
    LowRiskBrowserClickRequest,
    LowRiskBrowserClickStatus,
    LowRiskBrowserClickTransportResponse,
    build_low_risk_browser_click_decision,
    perform_low_risk_browser_click,
    validate_low_risk_browser_click_decision,
    validate_low_risk_browser_click_policy,
    validate_low_risk_browser_click_request,
    validate_low_risk_browser_click_result,
)


def _m93_decision():
    return build_multi_tool_dry_run_promotion_decision(_m93_request())


def _request(**overrides):
    m93_decision = overrides.pop("m93_promotion_decision", _m93_decision())
    data = {
        "request_ref": "low-risk-browser-click-request:m94",
        "click_ref": "low-risk-browser-click:m94-open-safe-details",
        "m93_promotion_decision_ref": m93_decision.decision_ref,
        "m93_promotion_decision": m93_decision,
        "actor_ref": m93_decision.actor_ref,
        "click_approval_ref": "approval:click-m94-safe-details",
        "scoped_session_ref": m93_decision.safe_execution_scope_ref,
        "allowed_page_ref": "browser-page:m94-docs-status",
        "allowed_action_ref": "browser-action:m94-open-safe-details",
        "observed_page_ref": "browser-observe-output:m94-redacted-page",
        "dry_run_plan_ref": m93_decision.dry_run_plan_ref,
        "safe_target_ref": "browser-target:m94-details-button",
        "low_risk_classification_ref": "risk-classification:m94-low-risk-click",
        "audit_ref": m93_decision.audit_ref,
        "replay_ref": m93_decision.replay_ref,
        "revocation_ref": "revocation:m94-click-window",
        "kill_switch_ref": "kill-switch:m94-click-window",
        "prior_milestone_refs": [
            "milestone:M73",
            "milestone:M75",
            "milestone:M91",
            "milestone:M92",
            "milestone:M93",
        ],
        "safe_click_summary": (
            "Activate a safe details disclosure on an allowlisted documentation page."
        ),
    }
    data.update(overrides)
    return LowRiskBrowserClickRequest(**data)


def _transport(_decision):
    return LowRiskBrowserClickTransportResponse(
        click_completed=True,
        safe_result_ref="browser-click-result:m94-safe-details-opened",
        safe_summary="Safe details disclosure was activated.",
    )


def test_m94_low_risk_browser_click_decision_is_exact_bound_and_safe() -> None:
    decision = build_low_risk_browser_click_decision(_request())

    assert decision.status == LowRiskBrowserClickStatus.click_allowed_for_scoped_session
    assert decision.low_risk_click_allowed is True
    assert decision.scoped_session_bound is True
    assert decision.allowlisted_page_bound is True
    assert decision.allowlisted_action_bound is True
    assert decision.exact_m93_promotion_bound is True
    assert decision.exact_click_approval_bound is True
    assert decision.audit_bound is True
    assert decision.revocation_bound is True
    assert decision.click_performed is False
    assert decision.form_submission_performed is False
    assert decision.typing_performed is False
    assert decision.purchase_performed is False
    assert decision.download_performed is False
    assert decision.authentication_performed is False
    assert decision.credential_or_cookie_access_performed is False
    assert decision.raw_dom_returned is False
    assert decision.screenshot_returned is False
    assert decision.external_network_performed is False
    assert decision.memory_write_performed is False
    assert decision.context_injection_performed is False
    assert decision.backend_route_added is False
    assert decision.production_authority_granted is False
    assert decision.side_effects_performed == []
    assert decision.receipt_plan.store_safe_summary_only is True
    assert decision.receipt_plan.store_safe_refs_only is True
    assert decision.reason_codes == [
        "M94_LOW_RISK_BROWSER_CLICK_ALLOWED",
        "M94_ALLOWLISTED_PAGE_REQUIRED",
        "M94_ALLOWLISTED_ACTION_REQUIRED",
        "M94_SCOPED_SESSION_REQUIRED",
        "M94_AUDIT_AND_REVOCATION_REQUIRED",
        "M95_REMAINS_FUTURE",
    ]


def test_m94_performs_click_only_through_injected_safe_transport() -> None:
    decision = build_low_risk_browser_click_decision(_request())

    with pytest.raises(ValueError, match="M94_BROWSER_CLICK_TRANSPORT_REQUIRED"):
        perform_low_risk_browser_click(decision, transport=None)

    result = perform_low_risk_browser_click(decision, transport=_transport)

    assert result.status == LowRiskBrowserClickStatus.click_completed
    assert result.click_performed is True
    assert result.raw_dom_returned is False
    assert result.screenshot_returned is False
    assert result.form_submission_performed is False
    assert result.typing_performed is False
    assert result.purchase_performed is False
    assert result.download_performed is False
    assert result.authentication_performed is False
    assert result.credential_or_cookie_access_performed is False
    assert result.external_network_performed is False
    assert result.memory_write_performed is False
    assert result.context_injection_performed is False
    assert result.production_authority_granted is False
    assert result.side_effects_performed == []
    assert result.reason_codes == [
        "M94_LOW_RISK_BROWSER_CLICK_COMPLETED",
        "M94_SAFE_RESULT_ONLY",
        "M94_AUDIT_AND_REVOCATION_REQUIRED",
    ]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("form_submission_requested", "FORM_SUBMISSION_DENIED"),
        ("typing_requested", "TYPING_DENIED"),
        ("purchase_requested", "PURCHASE_DENIED"),
        ("download_requested", "DOWNLOAD_DENIED"),
        ("upload_requested", "UPLOAD_DENIED"),
        ("authentication_requested", "AUTHENTICATION_DENIED"),
        ("account_change_requested", "ACCOUNT_CHANGE_DENIED"),
        ("destructive_action_requested", "DESTRUCTIVE_ACTION_DENIED"),
        ("credential_or_cookie_access_requested", "CREDENTIAL_OR_COOKIE_ACCESS_DENIED"),
        ("raw_dom_requested", "RAW_DOM_DENIED"),
        ("screenshot_requested", "SCREENSHOT_DENIED"),
        ("broad_navigation_requested", "BROAD_NAVIGATION_DENIED"),
        ("external_network_requested", "EXTERNAL_NETWORK_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
        ("contains_raw_dom", "RAW_DOM_DENIED"),
        ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
        ("contains_raw_provider_payload", "RAW_PROVIDER_PAYLOAD_DENIED"),
        ("contains_secret", "SECRET_LIKE_BROWSER_CLICK_CONTENT_DENIED"),
    ],
)
def test_m94_request_denies_unsafe_browser_actions_and_authority(
    field: str, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_low_risk_browser_click_request(_request(**{field: True}))


def test_m94_requires_exact_m93_binding_and_click_approval() -> None:
    for update, reason in [
        ({"m93_promotion_decision_ref": "multi-tool-dry-run-promotion-decision:other"}, "M94_M93_PROMOTION_BINDING_MISMATCH"),
        ({"actor_ref": "actor:other"}, "M94_ACTOR_BINDING_MISMATCH"),
        ({"scoped_session_ref": "scope:other"}, "M94_SCOPED_SESSION_BINDING_MISMATCH"),
        ({"audit_ref": "audit:other"}, "M94_AUDIT_BINDING_MISMATCH"),
        ({"replay_ref": "replay:other"}, "M94_REPLAY_BINDING_MISMATCH"),
        ({"click_approval_ref": "approval_test_:m94"}, "APPROVAL_TEST_REF_DENIED"),
        ({"click_approval_ref": "approval:click-m94-wildcard-all"}, "M94_WILDCARD_APPROVAL_DENIED"),
        ({"click_approval_ref": "approval:scope-only"}, "M94_EXACT_CLICK_APPROVAL_REQUIRED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            build_low_risk_browser_click_decision(_request(**update))


def test_m94_revalidates_model_copy_mutated_m93_decision_and_outputs() -> None:
    with pytest.raises(ValueError, match="M93_REAL_RUN_EXECUTION_DENIED"):
        build_low_risk_browser_click_decision(
            _request(
                m93_promotion_decision=_m93_decision().model_copy(
                    update={"real_run_execution_authorized": True}
                )
            )
        )

    decision = build_low_risk_browser_click_decision(_request())
    with pytest.raises(ValueError, match="M94_CLICK_NOT_ALLOWED_IN_DECISION"):
        validate_low_risk_browser_click_decision(decision.model_copy(update={"click_performed": True}))
    with pytest.raises(ValueError, match="RAW_DOM_DENIED"):
        validate_low_risk_browser_click_decision(
            decision.model_copy(
                update={
                    "receipt_plan": decision.receipt_plan.model_copy(
                        update={"store_raw_dom": True}
                    )
                }
            )
        )
    result = perform_low_risk_browser_click(decision, transport=_transport)
    with pytest.raises(ValueError, match="CREDENTIAL_OR_COOKIE_ACCESS_DENIED"):
        validate_low_risk_browser_click_result(
            result.model_copy(update={"credential_or_cookie_access_performed": True})
        )


def test_m94_transport_denies_hidden_unsafe_side_effects() -> None:
    decision = build_low_risk_browser_click_decision(_request())

    def unsafe_transport(_decision):
        return LowRiskBrowserClickTransportResponse(
            click_completed=True,
            safe_result_ref="browser-click-result:m94-unsafe",
            safe_summary="Unsafe click response.",
            form_submission_performed=True,
        )

    with pytest.raises(ValueError, match="FORM_SUBMISSION_DENIED"):
        perform_low_risk_browser_click(decision, transport=unsafe_transport)


def test_m94_policy_denies_unsafe_enablement_flags() -> None:
    for field, reason in [
        ("form_submission_allowed", "FORM_SUBMISSION_DENIED"),
        ("typing_allowed", "TYPING_DENIED"),
        ("purchase_allowed", "PURCHASE_DENIED"),
        ("download_allowed", "DOWNLOAD_DENIED"),
        ("authentication_allowed", "AUTHENTICATION_DENIED"),
        ("credential_or_cookie_access_allowed", "CREDENTIAL_OR_COOKIE_ACCESS_DENIED"),
        ("broad_navigation_allowed", "BROAD_NAVIGATION_DENIED"),
        ("external_network_allowed", "EXTERNAL_NETWORK_DENIED"),
        ("shell_execution_allowed", "SHELL_EXECUTION_DENIED"),
        ("plugin_execution_allowed", "PLUGIN_EXECUTION_DENIED"),
        ("production_authority_allowed", "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        with pytest.raises(ValueError, match=reason):
            validate_low_risk_browser_click_policy(LowRiskBrowserClickPolicy(**{field: True}))
