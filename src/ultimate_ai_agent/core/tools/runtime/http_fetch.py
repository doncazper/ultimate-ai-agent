from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
import hashlib
import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.tools.runtime.validation import (
    validate_safe_tool_runtime_text,
    validate_tool_runtime_ref,
)
from ultimate_ai_agent.core.web_access.contracts import (
    WebAccessAdapterKind,
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)
from ultimate_ai_agent.core.web_access.gateway import WebAccessGateway
from ultimate_ai_agent.core.web_access.policy import WebAccessPolicy


READ_ONLY_HTTP_FETCH_TOOL_REF = "tool:http_fetch.read_only_allowlisted.v1"
READ_ONLY_HTTP_FETCH_TOOL_NAME = "read_only_http_fetch"
DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES = 4096
DEFAULT_HTTP_FETCH_MAX_RESPONSE_BYTES = 65536
DEFAULT_HTTP_FETCH_TIMEOUT_SECONDS = 5

_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)\b(api[_-]?key|authorization|cookie|password|secret|token|client[_-]?secret)\b\s*[:=]\s*[^\s]+"
)
_BEARER_TOKEN_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}")
_PRIVATE_KEY_MARKER_RE = re.compile(r"-----" + r"BEGIN [A-Z ]*PRIVATE KEY" + r"-----")
_HIGH_ENTROPY_RE = re.compile(r"\b[A-Za-z0-9_/-]{32,}\b")
_UNSAFE_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SECRET_LIKE_URL_RE = re.compile(r"(?i)(api[_-]?key|authorization|bearer|cookie|password|secret|token|client[_-]?secret)")


class ReadOnlyHttpFetchStatus(str, Enum):
    preview_generated = "preview_generated"
    denied = "denied"
    transport_unavailable = "transport_unavailable"


class HttpFetchRedactionSummary(BaseModel):
    redaction_count: int = 0
    categories: list[str] = Field(default_factory=list)
    sensitive_values_returned: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_summary(self) -> Any:
        allowed_categories = {"secret_assignment", "bearer_token", "private_key_marker", "high_entropy_token"}
        if self.redaction_count < 0:
            raise ValueError("HTTP_FETCH_REDACTION_COUNT_INVALID")
        if any(category not in allowed_categories for category in self.categories):
            raise ValueError("HTTP_FETCH_REDACTION_CATEGORY_INVALID")
        if self.sensitive_values_returned:
            raise ValueError("HTTP_FETCH_REDACTION_SUMMARY_MUST_NOT_RETURN_SENSITIVE_VALUES")
        return self


class ReadOnlyHttpFetchPolicy(BaseModel):
    policy_ref: str = "http-fetch-policy:m72-read-only-allowlisted"
    read_only_http_fetch_allowed: bool = True
    allowlist_required: bool = True
    redaction_required: bool = True
    transport_injection_required: bool = True
    https_only: bool = True
    get_only: bool = True
    redirects_allowed: bool = False
    credentials_allowed: bool = False
    cookies_allowed: bool = False
    request_body_allowed: bool = False
    request_headers_allowed: bool = False
    query_string_allowed: bool = False
    raw_response_body_allowed: bool = False
    raw_headers_allowed: bool = False
    download_allowed: bool = False
    context_injection_allowed: bool = False
    memory_write_allowed: bool = False
    model_call_allowed: bool = False
    browser_automation_allowed: bool = False
    tool_execution_allowed: bool = False
    backend_route_allowed: bool = False
    production_authority_allowed: bool = False
    max_preview_bytes: int = DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES
    max_response_bytes: int = DEFAULT_HTTP_FETCH_MAX_RESPONSE_BYTES
    timeout_seconds: int = DEFAULT_HTTP_FETCH_TIMEOUT_SECONDS
    allowed_hosts: tuple[str, ...] = Field(default_factory=tuple)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_policy(self) -> Any:
        validate_tool_runtime_ref(self.policy_ref, "policy_ref")
        if not self.read_only_http_fetch_allowed:
            raise ValueError("READ_ONLY_HTTP_FETCH_POLICY_DISABLED")
        required_true = {
            "allowlist_required": self.allowlist_required,
            "redaction_required": self.redaction_required,
            "transport_injection_required": self.transport_injection_required,
            "https_only": self.https_only,
            "get_only": self.get_only,
        }
        for field_name, value in required_true.items():
            if not value:
                raise ValueError(f"{field_name.upper()}_REQUIRED")
        blocked_fields = [
            ("redirects_allowed", self.redirects_allowed, "REDIRECTS_DENIED"),
            ("credentials_allowed", self.credentials_allowed, "CREDENTIALS_DENIED"),
            ("cookies_allowed", self.cookies_allowed, "COOKIES_DENIED"),
            ("request_body_allowed", self.request_body_allowed, "REQUEST_BODY_DENIED"),
            ("request_headers_allowed", self.request_headers_allowed, "REQUEST_HEADERS_DENIED"),
            ("query_string_allowed", self.query_string_allowed, "QUERY_STRING_DENIED"),
            ("raw_response_body_allowed", self.raw_response_body_allowed, "RAW_RESPONSE_BODY_DENIED"),
            ("raw_headers_allowed", self.raw_headers_allowed, "RAW_HEADERS_DENIED"),
            ("download_allowed", self.download_allowed, "DOWNLOAD_DENIED"),
            ("context_injection_allowed", self.context_injection_allowed, "CONTEXT_INJECTION_DENIED"),
            ("memory_write_allowed", self.memory_write_allowed, "MEMORY_WRITE_DENIED"),
            ("model_call_allowed", self.model_call_allowed, "MODEL_CALL_DENIED"),
            ("browser_automation_allowed", self.browser_automation_allowed, "BROWSER_AUTOMATION_DENIED"),
            ("tool_execution_allowed", self.tool_execution_allowed, "TOOL_EXECUTION_DENIED"),
            ("backend_route_allowed", self.backend_route_allowed, "BACKEND_ROUTE_DENIED"),
            ("production_authority_allowed", self.production_authority_allowed, "PRODUCTION_AUTHORITY_DENIED"),
        ]
        for _field_name, value, reason in blocked_fields:
            if value:
                raise ValueError(reason)
        if not 1 <= self.max_preview_bytes <= DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES:
            raise ValueError("HTTP_FETCH_PREVIEW_BYTE_LIMIT_INVALID")
        if not self.max_preview_bytes <= self.max_response_bytes <= DEFAULT_HTTP_FETCH_MAX_RESPONSE_BYTES:
            raise ValueError("HTTP_FETCH_RESPONSE_BYTE_LIMIT_INVALID")
        if not 1 <= self.timeout_seconds <= DEFAULT_HTTP_FETCH_TIMEOUT_SECONDS:
            raise ValueError("HTTP_FETCH_TIMEOUT_LIMIT_INVALID")
        if not self.allowed_hosts:
            raise ValueError("HTTP_FETCH_ALLOWLIST_REQUIRED")
        normalized_hosts = tuple(_normalize_allowed_host(host) for host in self.allowed_hosts)
        if len(set(normalized_hosts)) != len(normalized_hosts):
            raise ValueError("HTTP_FETCH_ALLOWLIST_DUPLICATE_DENIED")
        object.__setattr__(self, "allowed_hosts", normalized_hosts)
        return self


class ReadOnlyHttpFetchRequest(BaseModel):
    request_ref: str = "http-fetch-request:m72"
    url: str
    method: str = "GET"
    allowed_host_policy_ref: str = "http-fetch-policy:m72-read-only-allowlisted"
    safe_summary: str = "Allowlisted read-only HTTP fetch."
    approval_ref: str | None = None
    authority_refs: list[str] = Field(default_factory=list)
    request_headers: dict[str, str] = Field(default_factory=dict)
    request_body: str | None = None
    include_raw_response_body: bool = False
    include_raw_headers: bool = False
    download_requested: bool = False
    context_injection_requested: bool = False
    memory_write_requested: bool = False
    model_call_requested: bool = False
    browser_automation_requested: bool = False
    tool_execution_requested: bool = False
    backend_route_requested: bool = False
    production_authority_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        validate_tool_runtime_ref(self.request_ref, "request_ref")
        validate_tool_runtime_ref(self.allowed_host_policy_ref, "allowed_host_policy_ref")
        validate_safe_tool_runtime_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_tool_runtime_text(self.approval_ref, "approval_ref")
        for ref in self.authority_refs:
            validate_tool_runtime_ref(ref, "authority_ref")
        return self


class ReadOnlyHttpFetchTransportResponse(BaseModel):
    status_code: int
    content_type: str = "text/plain"
    body: bytes
    final_url: str | None = None
    redirected: bool = False
    headers_present: bool = False
    cookies_present: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_response(self) -> Any:
        if not 100 <= self.status_code <= 599:
            raise ValueError("HTTP_FETCH_STATUS_INVALID")
        validate_safe_tool_runtime_text(self.content_type, "content_type")
        return self


class ReadOnlyHttpFetchOutput(BaseModel):
    output_ref: str
    safe_message: str = "READ_ONLY_HTTP_FETCH_REDACTED_PREVIEW_RETURNED"
    status: ReadOnlyHttpFetchStatus = ReadOnlyHttpFetchStatus.preview_generated
    request_ref: str
    safe_url_ref: str
    host_ref: str
    status_code: int
    content_type: str
    redacted_preview: str
    redaction_summary: HttpFetchRedactionSummary
    preview_truncated: bool = False
    preview_limit_bytes: int = DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES
    response_limit_bytes: int = DEFAULT_HTTP_FETCH_MAX_RESPONSE_BYTES
    response_bytes_read: int = 0
    fetch_performed: bool = True
    transport_ref: str = "http-fetch-transport:injected"
    real_world_transport_performed: bool = False
    web_access_audit_ref: str = "web-access-audit:unpersisted"
    web_access_request_ref: str = "web-access-request:unpersisted"
    web_access_audit_summary: dict[str, Any] = Field(default_factory=dict)
    raw_response_body_returned: bool = False
    raw_response_body_stored: bool = False
    raw_headers_returned: bool = False
    raw_headers_stored: bool = False
    absolute_url_returned: bool = False
    query_string_returned: bool = False
    credentials_or_cookies_used: bool = False
    request_body_sent: bool = False
    non_get_method_used: bool = False
    redirect_followed: bool = False
    download_performed: bool = False
    context_injection_performed: bool = False
    memory_write_performed: bool = False
    model_call_performed: bool = False
    browser_automation_performed: bool = False
    tool_execution_performed: bool = False
    backend_route_used: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_output(self) -> Any:
        for ref in [
            self.output_ref,
            self.request_ref,
            self.safe_url_ref,
            self.host_ref,
            self.transport_ref,
            self.web_access_audit_ref,
            self.web_access_request_ref,
        ]:
            validate_tool_runtime_ref(ref, "http_fetch_ref")
        validate_safe_tool_runtime_text(self.safe_message, "safe_message")
        validate_safe_tool_runtime_text(self.content_type, "content_type")
        if self.status != ReadOnlyHttpFetchStatus.preview_generated or not self.fetch_performed:
            raise ValueError("HTTP_FETCH_OUTPUT_INVALID")
        if not 100 <= self.status_code <= 599:
            raise ValueError("HTTP_FETCH_STATUS_INVALID")
        if _contains_unredacted_sensitive_preview(self.redacted_preview):
            raise ValueError("HTTP_FETCH_OUTPUT_CONTAINS_SECRET_LIKE_CONTENT")
        if self.preview_limit_bytes > DEFAULT_HTTP_FETCH_MAX_PREVIEW_BYTES:
            raise ValueError("HTTP_FETCH_PREVIEW_BYTE_LIMIT_INVALID")
        if self.response_limit_bytes > DEFAULT_HTTP_FETCH_MAX_RESPONSE_BYTES:
            raise ValueError("HTTP_FETCH_RESPONSE_BYTE_LIMIT_INVALID")
        unsafe_flags = [
            self.raw_response_body_returned,
            self.raw_response_body_stored,
            self.raw_headers_returned,
            self.raw_headers_stored,
            self.absolute_url_returned,
            self.query_string_returned,
            self.credentials_or_cookies_used,
            self.request_body_sent,
            self.non_get_method_used,
            self.redirect_followed,
            self.download_performed,
            self.context_injection_performed,
            self.memory_write_performed,
            self.model_call_performed,
            self.browser_automation_performed,
            self.tool_execution_performed,
            self.backend_route_used,
            self.production_authority_granted,
            self.side_effects_performed,
        ]
        if any(unsafe_flags):
            raise ValueError("HTTP_FETCH_OUTPUT_MUST_BE_REDACTED_READ_ONLY")
        return self


HttpFetchTransport = Callable[[ReadOnlyHttpFetchRequest, ReadOnlyHttpFetchPolicy], ReadOnlyHttpFetchTransportResponse]


@dataclass(frozen=True)
class NormalizedHttpFetchTarget:
    host: str
    path: str
    safe_url_ref: str
    host_ref: str


def http_fetch_policy_reason_codes(
    payload: Mapping[str, Any],
    policy: ReadOnlyHttpFetchPolicy | None = None,
) -> tuple[ReadOnlyHttpFetchRequest | None, NormalizedHttpFetchTarget | None, list[str]]:
    try:
        request = _request_from_payload(payload)
        active_policy = policy or ReadOnlyHttpFetchPolicy(
            allowed_hosts=_coerce_allowed_hosts(payload.get("allowed_hosts", ()))
        )
        target = normalize_http_fetch_target(request, active_policy)
    except ValueError as exc:
        return None, None, [_safe_reason(str(exc), "HTTP_FETCH_REQUEST_INVALID")]
    except Exception:
        return None, None, ["HTTP_FETCH_REQUEST_INVALID"]

    reasons = http_fetch_request_boundary_reason_codes(request)
    return request, target, list(dict.fromkeys(reasons))


def _request_from_payload(payload: Mapping[str, Any]) -> ReadOnlyHttpFetchRequest:
    allowed_fields = set(ReadOnlyHttpFetchRequest.model_fields)
    return ReadOnlyHttpFetchRequest.model_validate(
        {key: value for key, value in dict(payload).items() if key in allowed_fields}
    )


def http_fetch_request_boundary_reason_codes(request: ReadOnlyHttpFetchRequest) -> list[str]:
    reasons: list[str] = []
    if request.method.upper() != "GET":
        reasons.append("NON_GET_METHOD_DENIED")
    if request.approval_ref:
        reasons.append("APPROVAL_REF_NOT_AUTHORITY")
        if request.approval_ref.startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    for ref in request.authority_refs:
        if ref.startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
        if ref.split(":", 1)[0] in {
            "approval",
            "task-plan",
            "context-pack",
            "memory",
            "tool-intent",
            "model",
            "runtime",
            "openwebui",
            "control-center",
        }:
            reasons.append("AUTHORITY_REF_NOT_HTTP_FETCH_AUTHORITY")
    if request.request_headers:
        reasons.append("REQUEST_HEADERS_DENIED")
    if request.request_body is not None:
        reasons.append("REQUEST_BODY_DENIED")
    for flag, reason in [
        (request.include_raw_response_body, "RAW_RESPONSE_BODY_DENIED"),
        (request.include_raw_headers, "RAW_HEADERS_DENIED"),
        (request.download_requested, "DOWNLOAD_DENIED"),
        (request.context_injection_requested, "CONTEXT_INJECTION_DENIED"),
        (request.memory_write_requested, "MEMORY_WRITE_DENIED"),
        (request.model_call_requested, "MODEL_CALL_DENIED"),
        (request.browser_automation_requested, "BROWSER_AUTOMATION_DENIED"),
        (request.tool_execution_requested, "TOOL_EXECUTION_DENIED"),
        (request.backend_route_requested, "BACKEND_ROUTE_DENIED"),
        (request.production_authority_requested, "PRODUCTION_AUTHORITY_DENIED"),
    ]:
        if flag:
            reasons.append(reason)
    try:
        _validate_metadata_safe(request.metadata)
    except ValueError:
        reasons.append("SECRET_LIKE_HTTP_FETCH_METADATA_DENIED")
    return list(dict.fromkeys(reasons))


def normalize_http_fetch_target(
    request: ReadOnlyHttpFetchRequest,
    policy: ReadOnlyHttpFetchPolicy,
) -> NormalizedHttpFetchTarget:
    parts = urlsplit(request.url)
    if parts.scheme != "https":
        raise ValueError("HTTPS_ONLY_REQUIRED")
    if parts.username or parts.password:
        raise ValueError("URL_CREDENTIALS_DENIED")
    if not parts.hostname:
        raise ValueError("HTTP_FETCH_HOST_REQUIRED")
    host = _normalize_request_host(parts.hostname)
    if _host_is_ip_literal(host):
        raise ValueError("IP_LITERAL_HOST_DENIED")
    if host in {"localhost"} or host.endswith(".local"):
        raise ValueError("LOCAL_HOST_DENIED")
    if host not in set(policy.allowed_hosts):
        raise ValueError("HOST_NOT_ALLOWLISTED_DENIED")
    if parts.query:
        raise ValueError("QUERY_STRING_DENIED")
    if parts.fragment:
        raise ValueError("URL_FRAGMENT_DENIED")
    path = parts.path or "/"
    if not path.startswith("/"):
        raise ValueError("HTTP_FETCH_PATH_INVALID")
    if ".." in path.split("/"):
        raise ValueError("PATH_TRAVERSAL_DENIED")
    if _SECRET_LIKE_URL_RE.search(path):
        raise ValueError("SECRET_LIKE_URL_DENIED")
    return NormalizedHttpFetchTarget(
        host=host,
        path=path,
        safe_url_ref=_safe_url_ref(host, path),
        host_ref=f"http-fetch-host:{host.replace('.', '-')}",
    )


def _build_read_only_http_fetch_output(
    *,
    invocation_id: str,
    request: ReadOnlyHttpFetchRequest,
    policy: ReadOnlyHttpFetchPolicy,
    transport: HttpFetchTransport | None,
) -> ReadOnlyHttpFetchOutput:
    if transport is None:
        raise ValueError("HTTP_FETCH_TRANSPORT_REQUIRED")
    target = normalize_http_fetch_target(request, policy)
    reasons = http_fetch_request_boundary_reason_codes(request)
    if reasons:
        raise ValueError(reasons[0])
    response = ReadOnlyHttpFetchTransportResponse.model_validate(transport(request, policy))
    if response.redirected or response.final_url not in {None, request.url}:
        raise ValueError("REDIRECTS_DENIED")
    if response.headers_present:
        raise ValueError("RAW_HEADERS_DENIED")
    if response.cookies_present:
        raise ValueError("COOKIES_DENIED")
    if len(response.body) > policy.max_response_bytes:
        body = response.body[: policy.max_response_bytes]
    else:
        body = response.body
    if b"\x00" in body:
        raise ValueError("BINARY_RESPONSE_DENIED")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("UNSUPPORTED_RESPONSE_ENCODING_DENIED") from exc
    if _UNSAFE_CONTROL_CHAR_RE.search(text):
        raise ValueError("BINARY_RESPONSE_DENIED")
    preview_text = text[: policy.max_preview_bytes]
    redacted_preview, redaction_summary = _redact(preview_text)
    suffix = invocation_id.split(":", 1)[-1]
    transport_metadata = vars(transport) if hasattr(transport, "__dict__") else {}
    return ReadOnlyHttpFetchOutput(
        output_ref=f"http-fetch-output:{suffix}",
        request_ref=request.request_ref,
        safe_url_ref=target.safe_url_ref,
        host_ref=target.host_ref,
        status_code=response.status_code,
        content_type=response.content_type,
        redacted_preview=redacted_preview,
        redaction_summary=redaction_summary,
        transport_ref=str(
            transport_metadata.get("transport_ref", "http-fetch-transport:injected")
        ),
        real_world_transport_performed=bool(
            transport_metadata.get("real_world_transport_performed", False)
        ),
        preview_truncated=len(text) > policy.max_preview_bytes or len(response.body) > policy.max_response_bytes,
        preview_limit_bytes=policy.max_preview_bytes,
        response_limit_bytes=policy.max_response_bytes,
        response_bytes_read=len(body),
    )


@dataclass(frozen=True)
class _ToolRuntimeReadOnlyHttpFetchWebAccessAdapter:
    invocation_id: str
    fetch_request: ReadOnlyHttpFetchRequest
    policy: ReadOnlyHttpFetchPolicy
    transport: HttpFetchTransport | None

    adapter_kind: WebAccessAdapterKind = WebAccessAdapterKind.LOCAL_FETCH

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        if self.transport is None:
            return _blocked_http_fetch_adapter_result("HTTP_FETCH_TRANSPORT_REQUIRED")
        if request.kind != WebAccessRequestKind.READ_ONLY_FETCH:
            return _blocked_http_fetch_adapter_result("HTTP_FETCH_GATEWAY_KIND_MISMATCH")
        if request.method != "GET":
            return _blocked_http_fetch_adapter_result("NON_GET_METHOD_DENIED")
        try:
            output = _build_read_only_http_fetch_output(
                invocation_id=self.invocation_id,
                request=self.fetch_request,
                policy=self.policy,
                transport=self.transport,
            )
        except ValueError as exc:
            return _blocked_http_fetch_adapter_result(_safe_reason(str(exc), "HTTP_FETCH_REQUEST_INVALID"))

        return {
            "adapter_ref": "web-access-adapter:tool-runtime-read-only-http-fetch.v1",
            "allowed": True,
            "status": output.status.value,
            "safe_url_ref": output.safe_url_ref,
            "host_ref": output.host_ref,
            "output": output.model_dump(mode="python"),
            "preview": output.redacted_preview,
            "source_refs": [
                {
                    "safe_url_ref": output.safe_url_ref,
                    "host_ref": output.host_ref,
                    "content_untrusted": True,
                }
            ],
        }


def build_read_only_http_fetch_output_via_web_access_gateway(
    *,
    invocation_id: str,
    request: ReadOnlyHttpFetchRequest,
    policy: ReadOnlyHttpFetchPolicy,
    transport: HttpFetchTransport | None,
) -> ReadOnlyHttpFetchOutput:
    """Route the M72 read-only fetch primitive through WebAccessGateway."""

    adapter = _ToolRuntimeReadOnlyHttpFetchWebAccessAdapter(
        invocation_id=invocation_id,
        fetch_request=request,
        policy=policy,
        transport=transport,
    )
    gateway = WebAccessGateway(
        policy=WebAccessPolicy(allow_read_only_fetch=True),
        adapters={WebAccessRequestKind.READ_ONLY_FETCH: adapter},
    )
    result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.READ_ONLY_FETCH,
            url=request.url,
            method=request.method,
            authority_mode=WebAccessAuthorityMode.READ_ONLY,
            network_lane=WebAccessNetworkLane.TOOL_RUNTIME_READ_ONLY_FETCH,
            allowed_domains=policy.allowed_hosts,
            actor="tool_runtime",
            session_id=invocation_id,
            metadata={
                "adapter_ref": "web-access-adapter:tool-runtime-read-only-http-fetch.v1",
                "tool_ref": READ_ONLY_HTTP_FETCH_TOOL_REF,
                "request_ref": request.request_ref,
                "policy_ref": policy.policy_ref,
                "uses_auth": False,
                "cookies": False,
                "request_body": False,
                "download": False,
                "upload": False,
            },
        )
    )
    if result.status != WebAccessPolicyStatus.ALLOWED:
        raise ValueError(_http_fetch_reason_from_web_access_result(result.decision.reasons))

    payload = result.evidence_bundle.payload if result.evidence_bundle else {}
    output_payload = payload.get("output")
    if not isinstance(output_payload, Mapping):
        raise ValueError("HTTP_FETCH_GATEWAY_OUTPUT_MISSING")
    output = ReadOnlyHttpFetchOutput.model_validate(output_payload)
    safe_request_suffix = result.request_id.split(":", 1)[-1].replace("-", "")
    return output.model_copy(
        update={
            "web_access_request_ref": result.request_id,
            "web_access_audit_ref": f"web-access-audit:{safe_request_suffix}",
            "web_access_audit_summary": _redacted_web_access_audit_summary(
                result=result,
                safe_url_ref=output.safe_url_ref,
                host_ref=output.host_ref,
            ),
        }
    )


def _blocked_http_fetch_adapter_result(reason: str) -> Mapping[str, Any]:
    return {
        "adapter_ref": "web-access-adapter:tool-runtime-read-only-http-fetch.v1",
        "allowed": False,
        "status": "denied",
        "reason_codes": [reason],
    }


def _http_fetch_reason_from_web_access_result(reasons: tuple[str, ...]) -> str:
    for reason in reasons:
        if reason.startswith("adapter_reason:"):
            return _safe_reason(reason.split(":", 1)[1], "HTTP_FETCH_GATEWAY_DENIED")
    for reason in reasons:
        if reason == "adapter_policy_blocked":
            continue
        if reason.startswith("method_not_allowed:"):
            return "NON_GET_METHOD_DENIED"
        if reason == "only_https_urls_allowed":
            return "HTTPS_ONLY_REQUIRED"
        if reason == "missing_url_host":
            return "HTTP_FETCH_HOST_REQUIRED"
        if reason in {"private_or_local_network_denied", "host_not_in_allowed_domains"}:
            return "HOST_NOT_ALLOWLISTED_DENIED"
        if reason.startswith("network_lane_not_gateway_phase_1:"):
            return "HTTP_FETCH_GATEWAY_LANE_DENIED"
        if reason == "read_only_fetch_not_enabled":
            return "HTTP_FETCH_GATEWAY_DISABLED"
    return "HTTP_FETCH_GATEWAY_DENIED"


def _safe_reason(value: str, fallback: str) -> str:
    reason = value.strip().split("\n", 1)[0]
    if reason.isupper() and " " not in reason:
        return reason
    return fallback


def _normalize_allowed_host(value: str) -> str:
    host = _normalize_request_host(value)
    if "*" in host:
        raise ValueError("WILDCARD_HOST_DENIED")
    if _host_is_ip_literal(host) or host == "localhost" or host.endswith(".local"):
        raise ValueError("UNSAFE_ALLOWLIST_HOST_DENIED")
    if _SECRET_LIKE_URL_RE.search(host):
        raise ValueError("SECRET_LIKE_HOST_DENIED")
    return host


def _normalize_request_host(value: str) -> str:
    host = value.strip().lower().rstrip(".")
    if not host or "/" in host or ":" in host or "@" in host:
        raise ValueError("HTTP_FETCH_HOST_INVALID")
    validate_safe_tool_runtime_text(host, "host")
    return host


def _host_is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _safe_url_ref(host: str, path: str) -> str:
    normalized_path = path or "/"
    if normalized_path == "/":
        path_ref = "root"
    else:
        path_ref = f"path-{hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()[:16]}"
    return f"http-fetch-url:{host.replace('.', '-')}/{path_ref}"


def _redacted_web_access_audit_summary(
    *,
    result: Any,
    safe_url_ref: str,
    host_ref: str,
) -> dict[str, Any]:
    audit = result.audit
    policy_reasons = tuple(getattr(audit, "policy_reasons", ()) or ())
    return {
        "schema_version": "web-access-audit-summary.v1",
        "request_ref": result.request_id,
        "safe_url_ref": safe_url_ref,
        "host_ref": host_ref,
        "timestamp": audit.timestamp.isoformat(),
        "adapter_kind": audit.adapter_kind.value,
        "network_lane": audit.network_lane.value,
        "authority_mode": audit.authority_mode.value,
        "risk_class": audit.risk_class.value,
        "policy_status": audit.policy_status.value,
        "policy_reason_refs": [
            f"policy-reason:web-access:{_safe_ref_token(reason)}"
            for reason in policy_reasons
        ],
        "source_metadata_refs": [
            safe_url_ref,
            host_ref,
            "source-metadata:web-access:content-untrusted",
        ],
        "content_untrusted": True,
        "raw_url_omitted": True,
        "raw_headers_omitted": True,
        "raw_body_omitted": True,
    }


def _safe_ref_token(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_.-]", "-", value.strip().lower())
    token = token.strip("-")
    return token[:80] or "unknown"


def _coerce_allowed_hosts(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return tuple()


def _validate_metadata_safe(value: Any) -> None:
    if isinstance(value, str):
        validate_safe_tool_runtime_text(value, "metadata")
        return
    if isinstance(value, list):
        for item in value:
            _validate_metadata_safe(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_safe_tool_runtime_text(str(key), "metadata")
            _validate_metadata_safe(item)


def _contains_unredacted_sensitive_preview(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in [
            _SECRET_ASSIGNMENT_RE,
            _BEARER_TOKEN_RE,
            _PRIVATE_KEY_MARKER_RE,
            _HIGH_ENTROPY_RE,
        ]
    )


def _redact(text: str) -> tuple[str, HttpFetchRedactionSummary]:
    categories: list[str] = []

    def replace(pattern: re.Pattern[str], category: str, replacement: str, value: str) -> str:
        nonlocal categories
        if pattern.search(value):
            categories.append(category)
        return pattern.sub(replacement, value)

    redacted = text
    redacted = replace(_PRIVATE_KEY_MARKER_RE, "private_key_marker", "[REDACTED:PRIVATE_KEY_MARKER]", redacted)
    redacted = replace(_SECRET_ASSIGNMENT_RE, "secret_assignment", "[REDACTED:SECRET_ASSIGNMENT]", redacted)
    redacted = replace(_BEARER_TOKEN_RE, "bearer_token", "[REDACTED:BEARER_TOKEN]", redacted)
    redacted = replace(_HIGH_ENTROPY_RE, "high_entropy_token", "[REDACTED:HIGH_ENTROPY_TOKEN]", redacted)
    return redacted, HttpFetchRedactionSummary(
        redaction_count=len(categories),
        categories=list(dict.fromkeys(categories)),
    )
