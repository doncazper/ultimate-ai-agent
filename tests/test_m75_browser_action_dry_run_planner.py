from typing import Any

import pytest

import ultimate_ai_agent.core.browser as browser_core
import ultimate_ai_agent.core.browser.action_dry_run as action_dry_run
from ultimate_ai_agent.core.browser import (
    BrowserActionDryRunActionKind,
    BrowserActionDryRunPlannerPolicy,
    BrowserActionDryRunPlannerRequest,
    BrowserActionDryRunPlannerStatus,
    BrowserActionDryRunStep,
    build_browser_action_dry_run_plan_via_web_access_gateway,
    validate_browser_action_dry_run_policy,
)
from ultimate_ai_agent.core.web_access import (
    WebAccessAuthorityMode,
    WebAccessGateway,
    WebAccessNetworkLane,
    WebAccessPolicy,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)


def _step(**overrides: Any) -> Any:
    data = {
        "step_ref": "browser-action-step:m75-open-details",
        "action_kind": BrowserActionDryRunActionKind.click,
        "safe_target_ref": "browser-target:m75-details-button",
        "safe_intent": "Dry-run plan to activate the details button after user review.",
    }
    data.update(overrides)
    return BrowserActionDryRunStep(**data)


def _request(**overrides: Any) -> Any:
    data = {
        "plan_ref": "browser-action-plan:m75-safe",
        "actor_ref": "actor:local-reviewer",
        "target_ref": "browser-target:m75-docs-page",
        "source_observation_ref": "browser-observe-output:m74-safe",
        "safe_url_ref": "browser-url:docs-example-test/status",
        "safe_summary": "Plan a browser action without executing browser automation.",
        "steps": [_step()],
    }
    data.update(overrides)
    return BrowserActionDryRunPlannerRequest(**data)


def test_browser_action_dry_run_planner_builds_reviewable_plan_without_browser_control() -> None:
    plan = build_browser_action_dry_run_plan_via_web_access_gateway(_request())

    assert plan.status == BrowserActionDryRunPlannerStatus.plan_ready
    assert plan.plan_valid_for_review is True
    assert plan.dry_run_only is True
    assert plan.source_observation_content_untrusted is True
    assert plan.web_content_instruction_use_allowed is False
    assert plan.browser_action_execution_allowed is False
    assert plan.browser_action_execution_performed is False
    assert plan.browser_session_started is False
    assert plan.navigation_performed is False
    assert plan.click_performed is False
    assert plan.form_fill_performed is False
    assert plan.screenshot_returned is False
    assert plan.raw_dom_returned is False
    assert plan.authenticated_profile_used is False
    assert plan.cookies_or_credentials_used is False
    assert plan.network_call_performed is False
    assert plan.tool_execution_performed is False
    assert plan.memory_write_performed is False
    assert plan.context_injection_performed is False
    assert plan.backend_route_used is False
    assert plan.control_center_control_used is False
    assert plan.production_authority_granted is False
    assert plan.side_effects_performed == []
    assert [step.step_ref for step in plan.planned_steps] == ["browser-action-step:m75-open-details"]
    assert "M75_BROWSER_ACTION_DRY_RUN_PLAN" in plan.reason_codes
    assert "M76_REMAINS_FUTURE" in plan.reason_codes


def test_browser_action_package_exports_gateway_builder_not_direct_bypass() -> None:
    assert hasattr(browser_core, "build_browser_action_dry_run_plan_via_web_access_gateway")
    assert not hasattr(browser_core, "build_browser_action_dry_run_plan")


def test_browser_action_dry_run_routes_through_web_access_gateway(monkeypatch: Any) -> None:
    calls = []
    results = []
    original_execute = WebAccessGateway.execute

    def spy_execute(self: WebAccessGateway, request: Any) -> Any:
        calls.append((self, request))
        result = original_execute(self, request)
        results.append(result)
        return result

    monkeypatch.setattr(WebAccessGateway, "execute", spy_execute)

    plan = build_browser_action_dry_run_plan_via_web_access_gateway(_request())

    assert plan.status == BrowserActionDryRunPlannerStatus.plan_ready
    assert calls
    gateway, web_request = calls[0]
    assert gateway.policy.allow_browser_action_dry_run is True
    assert web_request.kind == WebAccessRequestKind.BROWSER_ACTION_DRY_RUN
    assert web_request.authority_mode == WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN
    assert web_request.network_lane == WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN
    assert web_request.url is None
    assert web_request.metadata["source_observation_ref"] == "browser-observe-output:m74-safe"
    assert web_request.metadata["source_observation_content_untrusted"] is True
    assert web_request.metadata["web_content_instruction_use_allowed"] is False
    assert results[0].evidence_bundle is not None
    evidence_payload = repr(results[0].evidence_bundle.payload)
    assert "https://" not in evidence_payload
    assert "browser-observe-output:m74-safe" in evidence_payload


def test_browser_action_execution_request_is_denied_before_planner_adapter(monkeypatch: Any) -> None:
    def forbidden_execute(self: Any, request: Any, decision: Any) -> Any:
        raise AssertionError("browser dry-run adapter must not run after gateway denial")

    monkeypatch.setattr(action_dry_run._BrowserActionDryRunWebAccessAdapter, "execute", forbidden_execute)

    plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(click_execution_requested=True)
    )

    assert plan.plan_valid_for_review is False
    assert plan.status == BrowserActionDryRunPlannerStatus.denied
    assert "BROWSER_CLICK_EXECUTION_DENIED" in plan.reason_codes


def test_browser_action_dry_run_adapter_requires_gateway_metadata_scope_match() -> None:
    planner_request = _request()
    adapter = action_dry_run._BrowserActionDryRunWebAccessAdapter(
        planner_request=planner_request,
        policy=BrowserActionDryRunPlannerPolicy(),
    )
    gateway = WebAccessGateway(
        policy=WebAccessPolicy(allow_browser_action_dry_run=True),
        adapters={WebAccessRequestKind.BROWSER_ACTION_DRY_RUN: adapter},
    )

    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.BROWSER_ACTION_DRY_RUN,
            method="GET",
            authority_mode=WebAccessAuthorityMode.BROWSER_ACTION_DRY_RUN,
            network_lane=WebAccessNetworkLane.BROWSER_ACTION_DRY_RUN,
            actor=planner_request.actor_ref,
            session_id=planner_request.plan_ref,
            metadata={
                "plan_ref": planner_request.plan_ref,
                "target_ref": planner_request.target_ref,
                "source_observation_ref": "browser-observe-output:other-safe",
                "safe_url_ref": planner_request.safe_url_ref,
                "source_observation_content_untrusted": True,
                "web_content_instruction_use_allowed": False,
            },
        )
    )

    assert result.status == WebAccessPolicyStatus.DENIED
    assert (
        "adapter_reason:BROWSER_ACTION_DRY_RUN_GATEWAY_METADATA_MISMATCH"
        in result.decision.reasons
    )


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("browser_action_execution_requested", "BROWSER_ACTION_EXECUTION_DENIED"),
        ("browser_session_start_requested", "BROWSER_SESSION_START_DENIED"),
        ("navigation_execution_requested", "BROWSER_NAVIGATION_EXECUTION_DENIED"),
        ("click_execution_requested", "BROWSER_CLICK_EXECUTION_DENIED"),
        ("form_fill_execution_requested", "FORM_FILL_EXECUTION_DENIED"),
        ("screenshot_requested", "SCREENSHOT_DENIED"),
        ("raw_dom_requested", "RAW_DOM_DENIED"),
        ("authenticated_profile_requested", "AUTHENTICATED_PROFILE_DENIED"),
        ("cookies_or_credentials_requested", "COOKIES_OR_CREDENTIALS_DENIED"),
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
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_browser_action_dry_run_planner_denies_execution_and_authority_flags(
    field: str, reason: str
) -> None:
    plan = build_browser_action_dry_run_plan_via_web_access_gateway(_request(**{field: True}))

    assert plan.plan_valid_for_review is False
    assert reason in plan.reason_codes


def test_browser_action_dry_run_planner_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "browser_action_execution_requested": True,
            "raw_dom_requested": True,
            "approval_ref": "approval:m75",
        }
    )

    plan = build_browser_action_dry_run_plan_via_web_access_gateway(request)

    assert plan.plan_valid_for_review is False
    assert "BROWSER_ACTION_EXECUTION_DENIED" in plan.reason_codes
    assert "APPROVAL_REF_NOT_AUTHORITY" in plan.reason_codes


def test_approval_and_context_refs_cannot_authorize_browser_action_plan() -> None:
    approval_plan = build_browser_action_dry_run_plan_via_web_access_gateway(_request(approval_ref="approval:m75"))
    assert approval_plan.plan_valid_for_review is False
    assert "APPROVAL_REF_NOT_AUTHORITY" in approval_plan.reason_codes

    approval_test_plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(approval_ref="approval_test_m75")
    )
    assert approval_test_plan.plan_valid_for_review is False
    assert "APPROVAL_TEST_REF_DENIED" in approval_test_plan.reason_codes

    authority_plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(authority_refs=["context-pack:m75"])
    )
    assert authority_plan.plan_valid_for_review is False
    assert "AUTHORITY_REF_NOT_BROWSER_ACTION_AUTHORITY" in authority_plan.reason_codes


def test_browser_action_dry_run_planner_denies_unsafe_steps_and_hidden_side_effects() -> None:
    execute_plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(steps=[_step(action_execution_performed=True)])
    )
    assert execute_plan.plan_valid_for_review is False
    assert "BROWSER_ACTION_EXECUTION_DENIED" in execute_plan.reason_codes

    raw_selector_plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(steps=[_step(safe_target_ref="/Users/sam/private-dom-node")])
    )
    assert raw_selector_plan.plan_valid_for_review is False
    assert "SECRET_LIKE_BROWSER_ACTION_CONTENT_DENIED" in raw_selector_plan.reason_codes

    duplicate_plan = build_browser_action_dry_run_plan_via_web_access_gateway(
        _request(steps=[_step(), _step(safe_target_ref="browser-target:m75-secondary")])
    )
    assert duplicate_plan.plan_valid_for_review is False
    assert "DUPLICATE_BROWSER_ACTION_STEP_REF_DENIED" in duplicate_plan.reason_codes


def test_browser_action_dry_run_planner_policy_denies_enablement() -> None:
    policy = BrowserActionDryRunPlannerPolicy(
        browser_action_execution_allowed=True,
        browser_session_start_allowed=True,
        production_authority_allowed=True,
    )

    with pytest.raises(ValueError, match="BROWSER_ACTION_EXECUTION_DENIED"):
        validate_browser_action_dry_run_policy(policy)
