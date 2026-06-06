import pytest

from ultimate_ai_agent.core.browser import (
    BrowserObserveOnlyAdapter,
    BrowserObserveOnlyObservation,
    BrowserObserveOnlyPolicy,
    BrowserObserveOnlyRequest,
    BrowserObserveOnlyStatus,
    build_browser_observe_only_output,
)


def _request(**overrides):
    data = {
        "request_ref": "browser-observe-request:m74-safe",
        "target_ref": "browser-target:m74-docs-status",
        "safe_url_ref": "browser-url:docs-example-test/status",
        "safe_summary": "Observe an already-open safe documentation page without browser control.",
    }
    data.update(overrides)
    return BrowserObserveOnlyRequest(**data)


def _observation(**overrides):
    data = {
        "title": "Docs status",
        "safe_url_ref": "browser-url:docs-example-test/status",
        "text_preview": "Public status ok\napi_key=super-secret-value\n",
        "visible_text_bytes": 48,
    }
    data.update(overrides)
    return BrowserObserveOnlyObservation(**data)


def _transport(_request, _policy):
    return _observation()


def test_browser_observe_only_adapter_redacts_preview_and_grants_no_control_authority() -> None:
    output = build_browser_observe_only_output(
        request=_request(),
        policy=BrowserObserveOnlyPolicy(),
        observe_transport=_transport,
    )

    assert output.status == BrowserObserveOnlyStatus.observation_ready
    assert output.observe_performed is True
    assert output.browser_automation_performed is False
    assert output.navigation_performed is False
    assert output.click_performed is False
    assert output.form_fill_performed is False
    assert output.screenshot_returned is False
    assert output.raw_dom_returned is False
    assert output.authenticated_profile_used is False
    assert output.cookies_or_credentials_used is False
    assert output.network_call_performed is False
    assert output.tool_execution_performed is False
    assert output.memory_write_performed is False
    assert output.context_injection_performed is False
    assert output.backend_route_used is False
    assert output.production_authority_granted is False
    assert output.side_effects_performed == []
    assert output.safe_url_ref == "browser-url:docs-example-test/status"
    assert "super-secret-value" not in output.redacted_text_preview
    assert "[REDACTED:SECRET_ASSIGNMENT]" in output.redacted_text_preview
    assert output.redaction_summary.redaction_count == 1
    assert "BROWSER_OBSERVE_ONLY_ADAPTER_OUTPUT" in output.reason_codes
    assert "M75_REMAINS_FUTURE" in output.reason_codes


def test_browser_observe_only_adapter_requires_explicit_transport() -> None:
    decision = BrowserObserveOnlyAdapter().observe(_request())

    assert decision.status == BrowserObserveOnlyStatus.transport_unavailable
    assert decision.observe_allowed is False
    assert "BROWSER_OBSERVE_TRANSPORT_REQUIRED" in decision.reason_codes


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("navigation_requested", "BROWSER_NAVIGATION_DENIED"),
        ("click_requested", "BROWSER_CLICK_DENIED"),
        ("form_fill_requested", "FORM_FILL_DENIED"),
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
def test_browser_observe_only_adapter_denies_control_and_authority_requests(
    field: str, reason: str
) -> None:
    decision = BrowserObserveOnlyAdapter().observe(
        _request(**{field: True}),
        observe_transport=_transport,
    )

    assert decision.observe_allowed is False
    assert reason in decision.reason_codes


def test_browser_observe_only_adapter_revalidates_model_copy_mutated_request() -> None:
    request = _request().model_copy(
        update={
            "click_requested": True,
            "raw_dom_requested": True,
            "approval_ref": "approval:m74",
        }
    )

    decision = BrowserObserveOnlyAdapter().observe(request, observe_transport=_transport)

    assert decision.observe_allowed is False
    assert "BROWSER_CLICK_DENIED" in decision.reason_codes


def test_browser_observe_only_adapter_denies_raw_snapshot_fields() -> None:
    decision = BrowserObserveOnlyAdapter().observe(
        _request(),
        observe_transport=lambda _request, _policy: _observation(raw_dom="<html>secret</html>"),
    )

    assert decision.observe_allowed is False
    assert "RAW_DOM_DENIED" in decision.reason_codes

    screenshot_decision = BrowserObserveOnlyAdapter().observe(
        _request(),
        observe_transport=lambda _request, _policy: _observation(screenshot_bytes=b"png"),
    )

    assert screenshot_decision.observe_allowed is False
    assert "SCREENSHOT_BYTES_DENIED" in screenshot_decision.reason_codes


def test_approval_refs_and_authority_refs_cannot_authorize_browser_observe() -> None:
    approval_decision = BrowserObserveOnlyAdapter().observe(
        _request(approval_ref="approval:m74"),
        observe_transport=_transport,
    )
    assert approval_decision.observe_allowed is False
    assert "APPROVAL_REF_NOT_AUTHORITY" in approval_decision.reason_codes

    approval_test_decision = BrowserObserveOnlyAdapter().observe(
        _request(approval_ref="approval_test_m74"),
        observe_transport=_transport,
    )
    assert approval_test_decision.observe_allowed is False
    assert "APPROVAL_TEST_REF_DENIED" in approval_test_decision.reason_codes

    authority_decision = BrowserObserveOnlyAdapter().observe(
        _request(authority_refs=["context-pack:m74"]),
        observe_transport=_transport,
    )
    assert authority_decision.observe_allowed is False
    assert "AUTHORITY_REF_NOT_BROWSER_OBSERVE_AUTHORITY" in authority_decision.reason_codes


def test_browser_observe_only_adapter_rejects_secret_like_metadata() -> None:
    decision = BrowserObserveOnlyAdapter().observe(
        _request(metadata={"session_cookie": "secret-value"}),
        observe_transport=_transport,
    )

    assert decision.observe_allowed is False
    assert "SECRET_LIKE_BROWSER_OBSERVE_CONTENT_DENIED" in decision.reason_codes
