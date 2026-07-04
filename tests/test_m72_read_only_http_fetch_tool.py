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
import ultimate_ai_agent.core.web_access.read_only_http_fetch_transport as real_world_transport
from ultimate_ai_agent.core.web_access.read_only_http_fetch_transport import (
    build_read_only_real_world_http_fetch_transport,
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


class _FakeTcpSocket:
    def __init__(self) -> None:
        self.timeout: float | None = None
        self.connected_to: Any | None = None
        self.closed = False

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def connect(self, sockaddr: Any) -> None:
        self.connected_to = sockaddr

    def close(self) -> None:
        self.closed = True


class _FakeTlsSocket:
    def __init__(self, response: bytes, peer_ip: str) -> None:
        self._response = response
        self._peer_ip = peer_ip
        self.sent = b""
        self.closed = False

    def getpeername(self) -> tuple[str, int]:
        return self._peer_ip, 443

    def sendall(self, payload: bytes) -> None:
        self.sent += payload

    def recv(self, limit: int) -> bytes:
        if not self._response:
            return b""
        chunk = self._response[:limit]
        self._response = self._response[limit:]
        return chunk

    def close(self) -> None:
        self.closed = True


class _FakeSslContext:
    def __init__(self, response: bytes, peer_ip: str) -> None:
        self.response = response
        self.peer_ip = peer_ip
        self.server_hostname: str | None = None
        self.tls_socket: _FakeTlsSocket | None = None

    def wrap_socket(self, _raw_socket: Any, *, server_hostname: str) -> _FakeTlsSocket:
        self.server_hostname = server_hostname
        self.tls_socket = _FakeTlsSocket(self.response, self.peer_ip)
        return self.tls_socket


def _http_response(
    *,
    status: int = 200,
    body: bytes = b"public status ok\napi_key=super-secret-value\n",
    headers: dict[str, str] | None = None,
) -> bytes:
    response_headers = {
        "Content-Type": "text/plain",
        "Content-Length": str(len(body)),
        "Connection": "close",
        **(headers or {}),
    }
    header_lines = [f"HTTP/1.1 {status} OK"]
    header_lines.extend(f"{name}: {value}" for name, value in response_headers.items())
    return ("\r\n".join(header_lines) + "\r\n\r\n").encode("ascii") + body


def _install_fake_real_world_peer(
    monkeypatch: Any,
    *,
    resolved_ip: str = "93.184.216.34",
    connected_peer_ip: str | None = None,
    response: bytes | None = None,
) -> tuple[_FakeTcpSocket, _FakeSslContext]:
    fake_tcp = _FakeTcpSocket()
    fake_context = _FakeSslContext(
        response or _http_response(),
        connected_peer_ip or resolved_ip,
    )
    monkeypatch.setattr(
        real_world_transport.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (
                real_world_transport.socket.AF_INET,
                real_world_transport.socket.SOCK_STREAM,
                6,
                "",
                (resolved_ip, 443),
            )
        ],
    )
    monkeypatch.setattr(
        real_world_transport.socket,
        "socket",
        lambda *_args, **_kwargs: fake_tcp,
    )
    monkeypatch.setattr(
        real_world_transport.ssl,
        "create_default_context",
        lambda: fake_context,
    )
    return fake_tcp, fake_context


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
    assert output.safe_url_ref.startswith("http-fetch-url:docs-example-test/path-")
    assert "/status" not in output.safe_url_ref
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


def test_read_only_real_world_transport_uses_gateway_and_safe_output(monkeypatch: Any) -> None:
    fake_tcp, fake_context = _install_fake_real_world_peer(monkeypatch)

    output = build_read_only_http_fetch_output_via_web_access_gateway(
        invocation_id="tool-runtime-invocation:m72-real-world",
        request=_fetch_request(),
        policy=_policy(),
        transport=build_read_only_real_world_http_fetch_transport(),
    )

    assert output.status == "preview_generated"
    assert output.fetch_performed is True
    assert output.real_world_transport_performed is True
    assert (
        output.transport_ref
        == "http-fetch-transport:web-access-gateway-real-world-v1"
    )
    assert output.web_access_audit_ref.startswith("web-access-audit:")
    assert output.web_access_request_ref.startswith("web-access-request:")
    assert output.safe_url_ref.startswith("http-fetch-url:docs-example-test/path-")
    assert "/status" not in output.safe_url_ref
    assert "https://docs.example.test/status" not in output.model_dump_json()
    assert "super-secret-value" not in output.redacted_preview
    assert "[REDACTED:SECRET_ASSIGNMENT]" in output.redacted_preview
    assert output.raw_response_body_stored is False
    assert output.raw_headers_stored is False
    assert output.redirect_followed is False
    assert output.browser_automation_performed is False
    assert output.context_injection_performed is False
    assert output.production_authority_granted is False
    assert fake_tcp.connected_to == ("93.184.216.34", 443)
    assert fake_tcp.closed is True
    assert fake_context.server_hostname == "docs.example.test"
    assert fake_context.tls_socket is not None
    assert b"GET /status HTTP/1.1\r\n" in fake_context.tls_socket.sent
    assert b"Host: docs.example.test\r\n" in fake_context.tls_socket.sent
    assert fake_context.tls_socket.closed is True


def test_read_only_real_world_transport_denies_private_dns_resolution(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        real_world_transport.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (
                real_world_transport.socket.AF_INET,
                real_world_transport.socket.SOCK_STREAM,
                6,
                "",
                ("10.0.0.2", 443),
            )
        ],
    )

    with pytest.raises(ValueError, match="PRIVATE_OR_LOCAL_RESOLVED_HOST_DENIED"):
        build_read_only_http_fetch_output_via_web_access_gateway(
            invocation_id="tool-runtime-invocation:m72-private-dns",
            request=_fetch_request(),
            policy=_policy(),
            transport=build_read_only_real_world_http_fetch_transport(),
        )


def test_read_only_real_world_transport_denies_private_connected_peer(monkeypatch: Any) -> None:
    _fake_tcp, fake_context = _install_fake_real_world_peer(
        monkeypatch,
        connected_peer_ip="10.0.0.2",
    )

    with pytest.raises(ValueError, match="PRIVATE_OR_LOCAL_RESOLVED_HOST_DENIED"):
        build_read_only_http_fetch_output_via_web_access_gateway(
            invocation_id="tool-runtime-invocation:m72-rebound-peer",
            request=_fetch_request(),
            policy=_policy(),
            transport=build_read_only_real_world_http_fetch_transport(),
        )

    assert fake_context.tls_socket is not None
    assert fake_context.tls_socket.sent == b""


def test_read_only_real_world_transport_decodes_bounded_chunked_response(monkeypatch: Any) -> None:
    chunked_response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"11\r\npublic status ok\n\r\n"
        b"1b\r\napi_key=super-secret-value\n\r\n"
        b"0\r\n\r\n"
    )
    _install_fake_real_world_peer(monkeypatch, response=chunked_response)

    output = build_read_only_http_fetch_output_via_web_access_gateway(
        invocation_id="tool-runtime-invocation:m72-chunked",
        request=_fetch_request(),
        policy=_policy(),
        transport=build_read_only_real_world_http_fetch_transport(),
    )

    assert output.real_world_transport_performed is True
    assert output.redacted_preview == "public status ok\n[REDACTED:SECRET_ASSIGNMENT]\n"
    assert "super-secret-value" not in output.model_dump_json()


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


def test_tool_runtime_adapter_reports_exact_real_world_network_truth(monkeypatch: Any) -> None:
    _fake_tcp, fake_context = _install_fake_real_world_peer(monkeypatch)

    decision = ToolRuntimeAdapter().invoke(
        _tool_request(),
        http_fetch_transport=build_read_only_real_world_http_fetch_transport(),
    )

    assert decision.status == ToolInvocationStatus.http_fetch_completed
    assert decision.invocation_allowed is True
    assert decision.execution_performed is True
    assert decision.network_call_performed is True
    assert decision.side_effects_performed == []
    assert decision.raw_content_stored is False
    assert decision.memory_write_performed is False
    assert decision.model_call_performed is False
    assert decision.shell_execution_performed is False
    assert decision.result is not None
    assert decision.result.network_call_performed is True
    assert decision.result.output.real_world_transport_performed is True
    assert (
        decision.result.output.transport_ref
        == "http-fetch-transport:web-access-gateway-real-world-v1"
    )
    assert "https://docs.example.test/status" not in decision.model_dump_json()
    assert "super-secret-value" not in decision.model_dump_json()
    assert fake_context.tls_socket is not None
    assert b"Host: docs.example.test\r\n" in fake_context.tls_socket.sent


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
    assert "http-fetch-url:docs-example-test/path-" in evidence_payload
    assert "http-fetch-url:docs-example-test/status" not in evidence_payload


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
    assert target.safe_url_ref.startswith("http-fetch-url:docs-example-test/path-")
    assert "/status" not in target.safe_url_ref
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
