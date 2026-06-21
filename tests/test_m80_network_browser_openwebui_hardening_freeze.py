from typing import Any
import pytest

from ultimate_ai_agent.core.hardening_freeze import (
    NetworkBrowserOpenWebUIFreezePolicy,
    NetworkBrowserOpenWebUIFreezeRequest,
    NetworkBrowserOpenWebUIFreezeStatus,
    build_network_browser_openwebui_freeze_report,
    validate_network_browser_openwebui_freeze_policy,
    validate_network_browser_openwebui_freeze_request,
)


def _request(**overrides: Any) -> Any:
    data = {
        "request_ref": "network-browser-openwebui-freeze-request:m80",
        "freeze_ref": "network-browser-openwebui-freeze:m80",
        "baseline_ref": "baseline:v0.83.0",
        "actor_ref": "actor:local-reviewer",
        "accepted_milestone_refs": [f"milestone:M{index}" for index in range(71, 80)],
        "checklist_refs": [
            "m80-freeze:m71-network-contract-reviewed",
            "m80-freeze:m72-allowlisted-redacted-fetch-only",
            "m80-freeze:m74-browser-observe-only",
            "m80-freeze:m75-browser-action-dry-run-only",
            "m80-freeze:m76-openwebui-bridge-review-only",
            "m80-freeze:m77-openwebui-handoff-exact-bound",
            "m80-freeze:m78-m79-plugin-disabled-by-default",
            "m80-freeze:route-stable",
            "m80-freeze:dependency-stable",
        ],
        "safe_summary": (
            "Freeze accepted network, browser, OpenWebUI, and plugin review boundaries "
            "without adding runtime authority."
        ),
    }
    data.update(overrides)
    return NetworkBrowserOpenWebUIFreezeRequest(**data)


def test_m80_freeze_report_is_review_only_and_no_authority() -> None:
    report = build_network_browser_openwebui_freeze_report(_request())

    assert report.status == NetworkBrowserOpenWebUIFreezeStatus.frozen
    assert report.freeze_only is True
    assert report.review_only is True
    assert report.network_browser_openwebui_only is True
    assert report.unrestricted_network_performed is False
    assert report.browser_action_performed is False
    assert report.openwebui_tool_execution_performed is False
    assert report.plugin_runtime_import_performed is False
    assert report.backend_route_added is False
    assert report.dependency_added is False
    assert report.production_authority_granted is False
    assert report.side_effects_performed == []
    assert report.reason_codes == [
        "M80_NETWORK_BROWSER_OPENWEBUI_HARDENING_FREEZE_REVIEW_ONLY",
        "M80_NO_NEW_RUNTIME_AUTHORITY",
        "M81_REMAINS_FUTURE",
    ]
    assert "private key" not in str(report.model_dump()).lower()


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("network_tool_expansion_requested", "NETWORK_TOOL_EXPANSION_DENIED"),
        ("unrestricted_network_requested", "UNRESTRICTED_NETWORK_DENIED"),
        ("authenticated_network_action_requested", "AUTHENTICATED_NETWORK_ACTION_DENIED"),
        ("raw_network_response_requested", "RAW_NETWORK_RESPONSE_DENIED"),
        ("browser_navigation_requested", "BROWSER_NAVIGATION_DENIED"),
        ("browser_click_requested", "BROWSER_CLICK_DENIED"),
        ("browser_action_execution_requested", "BROWSER_ACTION_EXECUTION_DENIED"),
        ("browser_screenshot_requested", "BROWSER_SCREENSHOT_DENIED"),
        ("raw_dom_requested", "RAW_DOM_DENIED"),
        ("authenticated_browser_profile_requested", "AUTHENTICATED_BROWSER_PROFILE_DENIED"),
        ("openwebui_model_authority_requested", "OPENWEBUI_MODEL_AUTHORITY_DENIED"),
        ("openwebui_tool_execution_requested", "OPENWEBUI_TOOL_EXECUTION_DENIED"),
        ("openwebui_memory_write_requested", "OPENWEBUI_MEMORY_WRITE_DENIED"),
        ("openwebui_context_injection_requested", "OPENWEBUI_CONTEXT_INJECTION_DENIED"),
        ("raw_prompt_exposure_requested", "RAW_PROMPT_EXPOSURE_DENIED"),
        ("raw_provider_payload_exposure_requested", "RAW_PROVIDER_PAYLOAD_EXPOSURE_DENIED"),
        ("plugin_install_requested", "PLUGIN_INSTALL_DENIED"),
        ("plugin_enablement_requested", "PLUGIN_ENABLEMENT_DENIED"),
        ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
        ("plugin_runtime_import_requested", "PLUGIN_RUNTIME_IMPORT_DENIED"),
        ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
        ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
        ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
        ("credential_cookie_access_requested", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
        ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
        ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
        ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_m80_freeze_denies_runtime_expansion_flags(field: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        validate_network_browser_openwebui_freeze_request(_request(**{field: True}))


def test_m80_freeze_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "browser_click_requested": True,
            "contains_secret": True,
        }
    )

    with pytest.raises(ValueError, match="BROWSER_CLICK_DENIED"):
        build_network_browser_openwebui_freeze_report(request)


def test_m80_freeze_requires_m71_through_m79_refs_and_unique_checklist() -> None:
    with pytest.raises(ValueError, match="M80_ACCEPTED_MILESTONES_REQUIRED"):
        validate_network_browser_openwebui_freeze_request(
            _request(accepted_milestone_refs=[])
        )

    with pytest.raises(ValueError, match="M80_MILESTONE_REF_REQUIRED"):
        validate_network_browser_openwebui_freeze_request(
            _request(accepted_milestone_refs=["milestone:M71"])
        )

    with pytest.raises(ValueError, match="M80_CHECKLIST_REF_DUPLICATE"):
        validate_network_browser_openwebui_freeze_request(
            _request(
                checklist_refs=[
                    "m80-freeze:route-stable",
                    "m80-freeze:route-stable",
                ]
            )
        )


def test_m80_freeze_denies_secret_like_metadata() -> None:
    request = _request(metadata={"token": "abcde12345678901234"})

    with pytest.raises(ValueError, match="SECRET_LIKE_M80_FREEZE_CONTENT_DENIED"):
        build_network_browser_openwebui_freeze_report(request)


def test_m80_freeze_policy_denies_enablement() -> None:
    policy = NetworkBrowserOpenWebUIFreezePolicy(
        unrestricted_network_enabled=True,
        browser_action_execution_enabled=True,
        openwebui_model_authority_enabled=True,
        remote_execution_enabled=True,
        production_authority_enabled=True,
    )

    with pytest.raises(ValueError, match="UNRESTRICTED_NETWORK_DENIED"):
        validate_network_browser_openwebui_freeze_policy(policy)
