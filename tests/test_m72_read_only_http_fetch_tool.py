from typing import Any

import pytest

import ultimate_ai_agent.core.tools.runtime as tool_runtime
from ultimate_ai_agent.core.tools.runtime import (
    READ_ONLY_HTTP_FETCH_TOOL_NAME,
    READ_ONLY_HTTP_FETCH_TOOL_REF,
    ReadOnlyHttpFetchPolicy,
    ReadOnlyHttpFetchRequest,
    ReadOnlyHttpFetchTransportResponse,
    ToolInvocationKind,
    ToolInvocationRequest,
    ToolInvocationStatus,
    ToolRuntimeAdapter,
    build_read_only_http_fetch_output_via_web_access_gateway,
    http_fetch_policy_reason_codes,
    normalize_http_fetch_target,
)
from ultimate_ai_agent.core.web_access import (
    WebAccessAuthorityMode,
    WebAccessGateway,
    WebAccessNetworkLane,
    WebAccessRequestKind,
)


def _policy(**overrides: Any) -> Any:
    data = {"allowed_hosts": ("docs.example.test",)}
    data.update(overrides)
    return ReadOnlyHttpFetchPolicy(**data)


def _fetch_request(**overrides: Any) -> Any:
    data = {
        "request_ref": "http-fetch-request:m72-safe",
        "url": "https://docs.example.test/status",
        "allowed_host_policy_ref": "http-fetch-policy:m72-read-only-allowlisted",
        "safe_summary": "Fetch a bounded redacted preview from an allowlisted documentation endpoint.",
    }
    data.update(overrides)
    return ReadOnlyHttpFetchRequest(**data)


def _tool_request(**metadata_overrides: Any) -> Any:
    metadata = {
        "request_ref": "http-fetch-request:m72-runtime",
        "url": "https://docs.example.test/status",
        "allowed_hosts": ["docs.example.test"],
        "allowed_host_policy_ref": "http-fetch-policy:m72-read-only-allowlisted",
        "safe_summary": "Fetch a bounded redacted preview from an allowlisted documentation endpoint.",
    }
    metadata.update(metadata_overrides)
    return ToolInvocationRequest(
        invocation_id="tool-runtime-invocation:m72-http-fetch",
        tool_ref=READ_ONLY_HTTP_FETCH_TOOL_REF,
        tool_name=READ_ONLY_HTTP_FETCH_TOOL_NAME,
        invocation_kind=ToolInvocationKind.read_only_http_fetch,
        replay_key="tool-runtime-replay:m72-http-fetch",
        safe_summary="Allowlisted read-only HTTP fetch.",
        metadata=metadata,
    )


def _fake_transport(_request: Any, _policy: Any) -> Any:
    return ReadOnlyHttpFetchTransportResponse(
        status_code=200,
        content_type="text/plain",
        body=b"public status ok\napi_key=super-secret-value\n",
    )


def test_read_only_http_fetch_gateway_redacts_before_return_and_stores_no_raw_body() -> None:
    output = build_read_only_http_fetch_output_via_web_access_gateway(
        invocation_id="tool-runtime-invocation:m72-direct",
        request=_fetch_request(),
        policy=_policy(),
        transport=_fake_transport,
    )

    assert output.status == "preview_generated"
    assert output.status_code == 200
    assert output.fetch_performed is True
    assert output.safe_url_ref == "http-fetch-url:docs-example-test/status"
    assert "super-secret-value" not in output.redacted_preview
    assert "[REDACTED:SECRET_ASSIGNMENT]" in output.redacted_preview
    assert output.redaction_summary.redaction_count == 1
    assert output.raw_response_body_returned is False
    assert output.raw_response_body_stored is False
    assert output.raw_headers_returned is False
    assert output.absolute_url_returned is False
    assert output.query_string_returned is False
    assert output.context_injection_performed is False
    assert output.memory_write_performed is False
    assert output.tool_execution_performed is False
    assert output.production_authority_granted is False
    assert output.side_effects_performed == []


def test_tool_runtime_package_exports_gateway_fetch_builder_not_direct_bypass() -> None:
    assert hasattr(tool_runtime, "build_read_only_http_fetch_output_via_web_access_gateway")
    assert not hasattr(tool_runtime, "build_read_only_http_fetch_output")


def test_tool_runtime_adapter_invokes_only_with_fake_transport_and_allowlisted_host() -> None:
    adapter = ToolRuntimeAdapter()

    decision = adapter.invoke(_tool_request(), http_fetch_transport=_fake_transport)

    assert decision.status == ToolInvocationStatus.http_fetch_completed
    assert decision.invocation_allowed is True
    assert decision.execution_performed is True
    assert decision.network_call_performed is False
    assert decision.raw_content_stored is False
    assert decision.memory_write_performed is False
    assert decision.result is not None
    assert decision.result.output.redacted_preview == "public status ok\n[REDACTED:SECRET_ASSIGNMENT]\n"
    assert decision.result.output.raw_response_body_stored is False
    assert "READ_ONLY_HTTP_FETCH_REDACTED_PREVIEW_RETURNED" in decision.reason_codes


def test_tool_runtime_http_fetch_routes_through_web_access_gateway(monkeypatch: Any) -> None:
    calls = []
    results = []
    original_execute = WebAccessGateway.execute

    def spy_execute(self: WebAccessGateway, request: Any) -> Any:
        calls.append((self, request))
        result = original_execute(self, request)
        results.append(result)
        return result

    monkeypatch.setattr(WebAccessGateway, "execute", spy_execute)

    decision = ToolRuntimeAdapter().invoke(_tool_request(), http_fetch_transport=_fake_transport)

    assert decision.invocation_allowed is True
    assert calls
    gateway, web_request = calls[0]
    assert gateway.policy.allow_read_only_fetch is True
    assert web_request.kind == WebAccessRequestKind.READ_ONLY_FETCH
    assert web_request.authority_mode == WebAccessAuthorityMode.READ_ONLY
    assert web_request.network_lane == WebAccessNetworkLane.TOOL_RUNTIME_READ_ONLY_FETCH
    assert web_request.allowed_domains == ("docs.example.test",)
    assert web_request.metadata["tool_ref"] == READ_ONLY_HTTP_FETCH_TOOL_REF
    assert results[0].evidence_bundle is not None
    evidence_payload = repr(results[0].evidence_bundle.payload)
    assert "https://docs.example.test/status" not in evidence_payload
    assert "http-fetch-url:docs-example-test/status" in evidence_payload


def test_tool_runtime_denies_http_fetch_without_transport() -> None:
    decision = ToolRuntimeAdapter().invoke(_tool_request())

    assert decision.invocation_allowed is False
    assert "HTTP_FETCH_TRANSPORT_REQUIRED" in decision.reason_codes


def test_tool_runtime_http_fetch_missing_transport_is_gateway_bound(monkeypatch: Any) -> None:
    calls = []
    original_execute = WebAccessGateway.execute

    def spy_execute(self: WebAccessGateway, request: Any) -> Any:
        calls.append(request)
        return original_execute(self, request)

    monkeypatch.setattr(WebAccessGateway, "execute", spy_execute)

    decision = ToolRuntimeAdapter().invoke(_tool_request())

    assert decision.invocation_allowed is False
    assert "HTTP_FETCH_TRANSPORT_REQUIRED" in decision.reason_codes
    assert calls
    assert calls[0].network_lane == WebAccessNetworkLane.TOOL_RUNTIME_READ_ONLY_FETCH


@pytest.mark.parametrize(
    ("metadata", "reason"),
    [
        ({"url": "http://docs.example.test/status"}, "HTTPS_ONLY_REQUIRED"),
        ({"url": "https://evil.example/status"}, "HOST_NOT_ALLOWLISTED_DENIED"),
        ({"url": "https://user:pass@docs.example.test/status"}, "URL_CREDENTIALS_DENIED"),
        ({"url": "https://docs.example.test/status?token=value"}, "QUERY_STRING_DENIED"),
        ({"url": "https://docs.example.test/secret-token"}, "SECRET_LIKE_URL_DENIED"),
        ({"url": "https://127.0.0.1/status", "allowed_hosts": ["127.0.0.1"]}, "UNSAFE_ALLOWLIST_HOST_DENIED"),
        ({"method": "POST"}, "NON_GET_METHOD_DENIED"),
        ({"request_headers": {"X-Test": "value"}}, "REQUEST_HEADERS_DENIED"),
        ({"request_body": "payload"}, "REQUEST_BODY_DENIED"),
        ({"include_raw_response_body": True}, "RAW_RESPONSE_BODY_DENIED"),
        ({"include_raw_headers": True}, "RAW_HEADERS_DENIED"),
        ({"download_requested": True}, "DOWNLOAD_DENIED"),
        ({"context_injection_requested": True}, "CONTEXT_INJECTION_DENIED"),
        ({"memory_write_requested": True}, "MEMORY_WRITE_DENIED"),
        ({"model_call_requested": True}, "MODEL_CALL_DENIED"),
        ({"browser_automation_requested": True}, "BROWSER_AUTOMATION_DENIED"),
        ({"tool_execution_requested": True}, "TOOL_EXECUTION_DENIED"),
        ({"production_authority_requested": True}, "PRODUCTION_AUTHORITY_DENIED"),
    ],
)
def test_http_fetch_policy_denies_unsafe_request_shapes(metadata: dict[str, object], reason: str) -> None:
    decision = ToolRuntimeAdapter().invoke(_tool_request(**metadata), http_fetch_transport=_fake_transport)

    assert decision.invocation_allowed is False
    assert reason in decision.reason_codes


def test_http_fetch_policy_requires_explicit_allowlist_and_rejects_wildcards() -> None:
    with pytest.raises(ValueError, match="HTTP_FETCH_ALLOWLIST_REQUIRED"):
        ReadOnlyHttpFetchPolicy()

    with pytest.raises(ValueError, match="WILDCARD_HOST_DENIED"):
        ReadOnlyHttpFetchPolicy(allowed_hosts=("*",))


def test_http_fetch_normalized_target_never_returns_absolute_url() -> None:
    target = normalize_http_fetch_target(_fetch_request(), _policy())

    assert target.host == "docs.example.test"
    assert target.path == "/status"
    assert target.safe_url_ref == "http-fetch-url:docs-example-test/status"
    assert "https://" not in target.safe_url_ref


def test_http_fetch_revalidates_model_copy_mutated_request_fields() -> None:
    request = _tool_request().model_copy(
        update={
            "metadata": {
                **_tool_request().metadata,
                "include_raw_response_body": True,
                "context_injection_requested": True,
            }
        }
    )

    decision = ToolRuntimeAdapter().invoke(request, http_fetch_transport=_fake_transport)

    assert decision.invocation_allowed is False
    assert "RAW_RESPONSE_BODY_DENIED" in decision.reason_codes


def test_approval_refs_and_authority_refs_cannot_authorize_http_fetch() -> None:
    approval_decision = ToolRuntimeAdapter().invoke(
        _tool_request(),
        http_fetch_transport=_fake_transport,
    )
    assert approval_decision.invocation_allowed is True

    with_approval_ref = _tool_request()
    with_approval_ref.approval_ref = "approval:m72"
    decision = ToolRuntimeAdapter().invoke(with_approval_ref, http_fetch_transport=_fake_transport)
    assert decision.invocation_allowed is False
    assert "APPROVAL_REF_NOT_AUTHORITY" in decision.reason_codes

    with_approval_test_ref = _tool_request()
    with_approval_test_ref.approval_ref = "approval_test_m72"
    decision = ToolRuntimeAdapter().invoke(with_approval_test_ref, http_fetch_transport=_fake_transport)
    assert decision.invocation_allowed is False
    assert "APPROVAL_TEST_REF_DENIED" in decision.reason_codes

    with_authority_ref = _tool_request()
    with_authority_ref.authority_refs = ["context-pack:m72"]
    decision = ToolRuntimeAdapter().invoke(with_authority_ref, http_fetch_transport=_fake_transport)
    assert decision.invocation_allowed is False
    assert "AUTHORITY_REF_NOT_TOOL_RUNTIME_AUTHORITY" in decision.reason_codes


def test_http_fetch_policy_reason_codes_are_stable() -> None:
    request, target, reasons = http_fetch_policy_reason_codes(
        {
            "request_ref": "http-fetch-request:m72-policy",
            "url": "https://docs.example.test/status",
            "allowed_hosts": ["docs.example.test"],
        }
    )

    assert request is not None
    assert target is not None
    assert reasons == []
