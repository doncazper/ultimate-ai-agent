from typing import Any
import pytest

from ultimate_ai_agent.core.browser import (
    BrowserActionDryRunActionKind,
    BrowserActionDryRunPlannerPolicy,
    BrowserActionDryRunPlannerRequest,
    BrowserActionDryRunPlannerStatus,
    BrowserActionDryRunStep,
    build_browser_action_dry_run_plan,
    validate_browser_action_dry_run_policy,
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
    plan = build_browser_action_dry_run_plan(_request())

    assert plan.status == BrowserActionDryRunPlannerStatus.plan_ready
    assert plan.plan_valid_for_review is True
    assert plan.dry_run_only is True
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
    plan = build_browser_action_dry_run_plan(_request(**{field: True}))

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

    plan = build_browser_action_dry_run_plan(request)

    assert plan.plan_valid_for_review is False
    assert "BROWSER_ACTION_EXECUTION_DENIED" in plan.reason_codes
    assert "APPROVAL_REF_NOT_AUTHORITY" in plan.reason_codes


def test_approval_and_context_refs_cannot_authorize_browser_action_plan() -> None:
    approval_plan = build_browser_action_dry_run_plan(_request(approval_ref="approval:m75"))
    assert approval_plan.plan_valid_for_review is False
    assert "APPROVAL_REF_NOT_AUTHORITY" in approval_plan.reason_codes

    approval_test_plan = build_browser_action_dry_run_plan(_request(approval_ref="approval_test_m75"))
    assert approval_test_plan.plan_valid_for_review is False
    assert "APPROVAL_TEST_REF_DENIED" in approval_test_plan.reason_codes

    authority_plan = build_browser_action_dry_run_plan(
        _request(authority_refs=["context-pack:m75"])
    )
    assert authority_plan.plan_valid_for_review is False
    assert "AUTHORITY_REF_NOT_BROWSER_ACTION_AUTHORITY" in authority_plan.reason_codes


def test_browser_action_dry_run_planner_denies_unsafe_steps_and_hidden_side_effects() -> None:
    execute_plan = build_browser_action_dry_run_plan(
        _request(steps=[_step(action_execution_performed=True)])
    )
    assert execute_plan.plan_valid_for_review is False
    assert "BROWSER_ACTION_EXECUTION_DENIED" in execute_plan.reason_codes

    raw_selector_plan = build_browser_action_dry_run_plan(
        _request(steps=[_step(safe_target_ref="/Users/sam/private-dom-node")])
    )
    assert raw_selector_plan.plan_valid_for_review is False
    assert "SECRET_LIKE_BROWSER_ACTION_CONTENT_DENIED" in raw_selector_plan.reason_codes

    duplicate_plan = build_browser_action_dry_run_plan(
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
