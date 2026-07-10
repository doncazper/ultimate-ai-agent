"""Exact governed self-hosted Firecrawl one-page markdown lane.

The public target remains an HTTPS GET with no body, auth, cookies, or mutable
semantics. Firecrawl's POST is a separate fixed loopback provider transport.
Every attempt is single-use and follows current availability, PolicyEngine,
exact LocalApprovalAuthority, exact resource-constrained AuthorityLease, target
validation, WebAccessGateway policy, and redacted receipt checks.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import threading
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal, Mapping, Sequence
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityCapability,
    AuthorityConstraintKind,
    AuthorityDomain,
    AuthorityLease,
    AuthorityPolicyDecision,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.capabilities.approval import LocalApprovalAuthority
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityAuthorityLevel,
    CapabilityCostClass,
    CapabilityKind,
    CapabilityPrivacyLevel,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityManifest,
    RuntimePolicy,
    SafetyPolicy,
    TaskEnvelope,
)
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.capability_availability import (
    CapabilityAvailabilitySnapshot,
    CapabilityInvocationDecision,
    CapabilityInvocationRequest,
    CostPosture,
    IdempotencyPosture,
    InvocationDecisionOutcome,
    build_capability_availability_snapshot,
    evaluate_capability_invocation,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.observability.debug_logs import redact_debug_text
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    SourceMetadata,
    WebAccessAdapterKind,
    WebAccessAuthorityMode,
    WebAccessNetworkLane,
    WebAccessPolicyDecision,
    WebAccessPolicyStatus,
    WebAccessRequest,
    WebAccessRequestKind,
)
from .gateway import WebAccessGateway
from .hybrid_contracts import (
    WebProviderCapabilityState,
    WebProviderDeploymentKind,
    WebProviderOperation,
    WebProviderTransportMethod,
    WebProviderTransportReceipt,
    WebProviderTransportStatus,
    stable_web_hybrid_ref,
)
from .policy import WebAccessPolicy


FIRECRAWL_MARKDOWN_CAPABILITY_REF = (
    "capability-ref:web-access:firecrawl-markdown-extract"
)
FIRECRAWL_SELF_HOSTED_PROVIDER_REF = "provider-ref:firecrawl:self-hosted"
FIRECRAWL_MARKDOWN_ADAPTER_REF = "adapter-ref:web-access:firecrawl-markdown-extract:v1"
FIRECRAWL_MARKDOWN_LANE_REF = (
    "authority-lane-ref:web-access:firecrawl-markdown-extract:v1"
)
FIRECRAWL_SELF_HOSTED_ENDPOINT_REF = (
    "configured-endpoint-ref:firecrawl:self-hosted-loopback"
)
FIRECRAWL_MARKDOWN_REQUEST_SCHEMA_REF = (
    "schema-ref:firecrawl-markdown-extract-request:v1"
)
FIRECRAWL_NOT_METERED_BUDGET_REF = (
    "budget-decision-ref:not-metered:firecrawl-self-hosted"
)
FIRECRAWL_SELF_HOSTED_DEFAULT_ENDPOINT = "http://127.0.0.1:3002"
FIRECRAWL_MAX_RESPONSE_BYTES = 2_097_152
FIRECRAWL_MAX_MARKDOWN_CHARS = 200_000
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


class FirecrawlPreviewRedactionStatus(str, Enum):
    bounded = "bounded"
    redacted = "redacted"
    withheld = "withheld"


class _FirecrawlModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class FirecrawlMarkdownRequest(_FirecrawlModel):
    request_ref: str
    task_ref: str
    approval_ref: str | None = None
    target_url: str = Field(..., min_length=1, max_length=2048)
    target_source_ref: str
    allowed_domains: tuple[str, ...] = Field(..., min_length=1, max_length=5)
    max_markdown_chars: int = Field(
        default=100_000,
        ge=1_024,
        le=FIRECRAWL_MAX_MARKDOWN_CHARS,
    )
    page_count: Literal[1] = 1
    attempt_count: Literal[1] = 1
    expected_execution_receipt_ref: str

    @field_validator(
        "request_ref",
        "task_ref",
        "approval_ref",
        "target_source_ref",
        "expected_execution_receipt_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        if value is not None:
            validate_execution_ref(value, "firecrawl_markdown_ref")
        return value

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(
            dict.fromkeys(value.strip().lower().rstrip(".") for value in values)
        )
        if not normalized or any(not _public_domain(value) for value in normalized):
            raise ValueError("FIRECRAWL_ALLOWED_DOMAIN_INVALID")
        return normalized

    @model_validator(mode="after")
    def validate_target(self) -> "FirecrawlMarkdownRequest":
        host = _validated_target_syntax(self.target_url)
        if not _host_matches_allowed_domains(host, self.allowed_domains):
            raise ValueError("FIRECRAWL_TARGET_HOST_NOT_ALLOWED")
        if self.target_source_ref != firecrawl_target_source_ref(self.target_url):
            raise ValueError("FIRECRAWL_TARGET_SOURCE_REF_MISMATCH")
        return self


class FirecrawlConfiguredEndpoint(_FirecrawlModel):
    endpoint_ref: Literal["configured-endpoint-ref:firecrawl:self-hosted-loopback"] = (
        FIRECRAWL_SELF_HOSTED_ENDPOINT_REF
    )
    base_url: str = FIRECRAWL_SELF_HOSTED_DEFAULT_ENDPOINT
    timeout_seconds: float = Field(default=45.0, gt=0, le=60)
    max_response_bytes: int = Field(
        default=FIRECRAWL_MAX_RESPONSE_BYTES,
        ge=1_024,
        le=FIRECRAWL_MAX_RESPONSE_BYTES,
    )

    @model_validator(mode="after")
    def validate_fixed_loopback_endpoint(self) -> "FirecrawlConfiguredEndpoint":
        parts = urlsplit(self.base_url)
        try:
            port = parts.port
        except ValueError as exc:
            raise ValueError("FIRECRAWL_CONFIGURED_LOOPBACK_ENDPOINT_REQUIRED") from exc
        if (
            parts.scheme != "http"
            or parts.hostname != "127.0.0.1"
            or parts.username is not None
            or parts.password is not None
            or parts.path not in {"", "/"}
            or parts.query
            or parts.fragment
            or port is None
        ):
            raise ValueError("FIRECRAWL_CONFIGURED_LOOPBACK_ENDPOINT_REQUIRED")
        return self


class FirecrawlMarkdownEvidence(_FirecrawlModel):
    source_ref: str
    target_url: str = Field(..., min_length=1, max_length=2048)
    final_url: str = Field(..., min_length=1, max_length=2048)
    host: str = Field(..., min_length=1, max_length=253)
    title: str = Field(default="", max_length=240)
    markdown: str = Field(..., min_length=1, max_length=FIRECRAWL_MAX_MARKDOWN_CHARS)
    content_hash_ref: str
    bounded_redacted_preview: str = Field(..., min_length=1, max_length=500)
    preview_redaction_status: FirecrawlPreviewRedactionStatus
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False
    memory_write_allowed: Literal[False] = False
    context_injection_allowed: Literal[False] = False
    raw_html_returned: Literal[False] = False
    raw_dom_returned: Literal[False] = False
    screenshot_returned: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence(self) -> "FirecrawlMarkdownEvidence":
        validate_execution_ref(self.source_ref, "firecrawl_source_ref")
        validate_execution_ref(self.content_hash_ref, "firecrawl_content_hash_ref")
        target_host = _validated_target_syntax(self.target_url)
        final_host = _validated_target_syntax(self.final_url)
        if target_host != self.host or final_host != self.host:
            raise ValueError("FIRECRAWL_EVIDENCE_HOST_MISMATCH")
        if self.source_ref != firecrawl_target_source_ref(self.target_url):
            raise ValueError("FIRECRAWL_EVIDENCE_SOURCE_REF_MISMATCH")
        if self.content_hash_ref != _markdown_hash_ref(self.markdown):
            raise ValueError("FIRECRAWL_EVIDENCE_CONTENT_HASH_MISMATCH")
        if contains_secret_like(
            self.bounded_redacted_preview
        ) or contains_obvious_secret(self.bounded_redacted_preview):
            raise ValueError("FIRECRAWL_PREVIEW_SECRET_LIKE_CONTENT_DENIED")
        return self


class FirecrawlMarkdownExecutionResult(_FirecrawlModel):
    request_ref: str
    task_ref: str
    invocation_decision: CapabilityInvocationDecision
    transport_receipt: WebProviderTransportReceipt
    gateway_audit_ref: str
    status: WebProviderTransportStatus
    evidence: FirecrawlMarkdownEvidence | None = None
    execution_succeeded: bool = False
    reason_codes: tuple[str, ...] = ()
    blocker_codes: tuple[str, ...] = ()
    content_untrusted: Literal[True] = True
    instruction_use_allowed: Literal[False] = False
    raw_target_stored: Literal[False] = False
    raw_page_stored: Literal[False] = False
    raw_provider_payload_stored: Literal[False] = False
    raw_html_stored: Literal[False] = False
    credential_material_stored: Literal[False] = False
    local_path_stored: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> "FirecrawlMarkdownExecutionResult":
        for value in (self.request_ref, self.task_ref, self.gateway_audit_ref):
            validate_execution_ref(value, "firecrawl_execution_ref")
        for code in (*self.reason_codes, *self.blocker_codes):
            if not _SAFE_CODE.fullmatch(code):
                raise ValueError("FIRECRAWL_EXECUTION_CODE_UNSAFE")
        succeeded = self.status == WebProviderTransportStatus.succeeded
        if self.execution_succeeded != succeeded:
            raise ValueError("FIRECRAWL_EXECUTION_STATUS_MISMATCH")
        if (
            succeeded
            and self.invocation_decision.outcome != InvocationDecisionOutcome.allow
        ):
            raise ValueError("FIRECRAWL_EXECUTION_WITHOUT_INVOCATION_AUTHORITY")
        if (
            self.status
            not in {
                WebProviderTransportStatus.succeeded,
                WebProviderTransportStatus.simulated,
            }
            and self.evidence is not None
        ):
            raise ValueError("FIRECRAWL_NON_SUCCESS_EVIDENCE_DENIED")
        return self


class FirecrawlMarkdownAttemptResult(_FirecrawlModel):
    status: WebProviderTransportStatus
    evidence: FirecrawlMarkdownEvidence | None = None
    reason_codes: tuple[str, ...] = ()
    network_call_performed: bool = False
    gateway_audit_ref: str

    @model_validator(mode="after")
    def validate_attempt(self) -> "FirecrawlMarkdownAttemptResult":
        validate_execution_ref(self.gateway_audit_ref, "firecrawl_gateway_audit_ref")
        for code in self.reason_codes:
            if not _SAFE_CODE.fullmatch(code):
                raise ValueError("FIRECRAWL_ATTEMPT_CODE_UNSAFE")
        if self.status in {
            WebProviderTransportStatus.blocked,
            WebProviderTransportStatus.simulated,
        } and self.network_call_performed:
            raise ValueError("FIRECRAWL_ATTEMPT_NETWORK_STATUS_MISMATCH")
        if self.status not in {
            WebProviderTransportStatus.succeeded,
            WebProviderTransportStatus.simulated,
        } and self.evidence is not None:
            raise ValueError("FIRECRAWL_ATTEMPT_EVIDENCE_STATUS_MISMATCH")
        return self


class FirecrawlTransportError(RuntimeError):
    def __init__(self, code: str, *, network_call_performed: bool) -> None:
        if not _SAFE_CODE.fullmatch(code):
            raise ValueError("FIRECRAWL_TRANSPORT_ERROR_CODE_UNSAFE")
        super().__init__(code)
        self.code = code
        self.network_call_performed = network_call_performed


FirecrawlTransport = Callable[[FirecrawlMarkdownRequest], Mapping[str, Any]]
TargetValidator = Callable[[str], None]


def build_loopback_firecrawl_transport(
    endpoint: FirecrawlConfiguredEndpoint | None = None,
) -> FirecrawlTransport:
    configured = endpoint or FirecrawlConfiguredEndpoint()
    parts = urlsplit(configured.base_url)
    host = parts.hostname or ""
    port = parts.port or 80

    def transport(request: FirecrawlMarkdownRequest) -> Mapping[str, Any]:
        body = json.dumps(
            {
                "url": request.target_url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "timeout": 15_000,
                "waitFor": 0,
                "maxAge": 0,
                "storeInCache": False,
                "removeBase64Images": True,
                "blockAds": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(body) > 4_096:
            raise FirecrawlTransportError(
                "FIRECRAWL_REQUEST_BODY_TOO_LARGE",
                network_call_performed=False,
            )
        status, content_type, response_body = _loopback_json_post(
            host=host,
            port=port,
            path="/v2/scrape",
            body=body,
            timeout_seconds=configured.timeout_seconds,
            max_response_bytes=configured.max_response_bytes,
        )
        if 300 <= status <= 399:
            raise FirecrawlTransportError(
                "FIRECRAWL_PROVIDER_REDIRECT_DENIED",
                network_call_performed=True,
            )
        if status != 200:
            raise FirecrawlTransportError(
                _provider_http_status_code(status),
                network_call_performed=True,
            )
        if content_type.split(";", 1)[0].strip().lower() != "application/json":
            raise FirecrawlTransportError(
                "FIRECRAWL_PROVIDER_JSON_RESPONSE_REQUIRED",
                network_call_performed=True,
            )
        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FirecrawlTransportError(
                "FIRECRAWL_PROVIDER_RESPONSE_JSON_INVALID",
                network_call_performed=True,
            ) from exc
        if not isinstance(payload, Mapping):
            raise FirecrawlTransportError(
                "FIRECRAWL_PROVIDER_RESPONSE_OBJECT_REQUIRED",
                network_call_performed=True,
            )
        return payload

    transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    transport.configured_endpoint_ref = configured.endpoint_ref  # type: ignore[attr-defined]
    return transport


def _provider_http_status_code(status: int) -> str:
    if status in {400, 401, 403, 404, 409, 422, 429}:
        return f"FIRECRAWL_PROVIDER_HTTP_{status}"
    if 500 <= status <= 599:
        return "FIRECRAWL_PROVIDER_HTTP_5XX"
    return "FIRECRAWL_PROVIDER_NON_SUCCESS_STATUS"


def _loopback_json_post(
    *,
    host: str,
    port: int,
    path: str,
    body: bytes,
    timeout_seconds: float,
    max_response_bytes: int,
) -> tuple[int, str, bytes]:
    request_bytes = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Accept: application/json\r\n"
        "Accept-Encoding: identity\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "User-Agent: ultimate-ai-agent-firecrawl-markdown/1\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii") + body
    attempted = False
    try:
        with socket.create_connection(
            (host, port), timeout=timeout_seconds
        ) as connection:
            attempted = True
            connection.settimeout(timeout_seconds)
            connection.sendall(request_bytes)
            raw = bytearray()
            header_end = -1
            while header_end < 0:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                raw.extend(chunk)
                header_end = raw.find(b"\r\n\r\n")
                if len(raw) > 32_768:
                    raise FirecrawlTransportError(
                        "FIRECRAWL_PROVIDER_RESPONSE_HEADERS_TOO_LARGE",
                        network_call_performed=True,
                    )
            if header_end < 0:
                raise FirecrawlTransportError(
                    "FIRECRAWL_PROVIDER_RESPONSE_HEADERS_INVALID",
                    network_call_performed=True,
                )
            status, headers = _parse_response_headers(bytes(raw[:header_end]))
            response_body = bytearray(raw[header_end + 4 :])
            if headers.get("content-encoding", "identity").lower() not in {
                "",
                "identity",
            }:
                raise FirecrawlTransportError(
                    "FIRECRAWL_PROVIDER_RESPONSE_ENCODING_DENIED",
                    network_call_performed=True,
                )
            if headers.get("transfer-encoding", "").lower() not in {"", "identity"}:
                raise FirecrawlTransportError(
                    "FIRECRAWL_PROVIDER_TRANSFER_ENCODING_DENIED",
                    network_call_performed=True,
                )
            while len(response_body) <= max_response_bytes:
                chunk = connection.recv(
                    min(4096, max_response_bytes + 1 - len(response_body))
                )
                if not chunk:
                    break
                response_body.extend(chunk)
            if len(response_body) > max_response_bytes:
                raise FirecrawlTransportError(
                    "FIRECRAWL_PROVIDER_RESPONSE_TOO_LARGE",
                    network_call_performed=True,
                )
        return status, headers.get("content-type", ""), bytes(response_body)
    except FirecrawlTransportError:
        raise
    except (OSError, TimeoutError) as exc:
        raise FirecrawlTransportError(
            "FIRECRAWL_PROVIDER_TRANSPORT_FAILED",
            network_call_performed=attempted,
        ) from exc


def _parse_response_headers(header_bytes: bytes) -> tuple[int, dict[str, str]]:
    try:
        lines = header_bytes.decode("iso-8859-1").split("\r\n")
        status_parts = lines[0].split(None, 2)
        status = int(status_parts[1])
    except (IndexError, UnicodeDecodeError, ValueError) as exc:
        raise FirecrawlTransportError(
            "FIRECRAWL_PROVIDER_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        ) from exc
    if len(status_parts) < 2 or not status_parts[0].startswith("HTTP/"):
        raise FirecrawlTransportError(
            "FIRECRAWL_PROVIDER_RESPONSE_STATUS_INVALID",
            network_call_performed=True,
        )
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            raise FirecrawlTransportError(
                "FIRECRAWL_PROVIDER_RESPONSE_HEADERS_INVALID",
                network_call_performed=True,
            )
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return status, headers


def build_firecrawl_markdown_capability_manifest() -> CapabilityManifest:
    return CapabilityManifest(
        id=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        version="1.0.0",
        kind=CapabilityKind.tool,
        name="Firecrawl governed one-page markdown extraction",
        description="Extract bounded transient markdown from one exact public HTTPS target.",
        examples=["Extract one approved public page into untrusted markdown evidence."],
        anti_examples=[
            "Do not crawl, map, interact, authenticate, or retain raw page data."
        ],
        input_schema={
            "type": "object",
            "required": ["target_source_ref", "allowed_domains"],
            "properties": {
                "target_source_ref": {"type": "string"},
                "allowed_domains": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 5,
                },
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "required": ["transient_markdown_evidence", "transport_receipt"],
            "additionalProperties": False,
        },
        input_modes=["ephemeral_target_url", "safe_target_source_ref"],
        output_modes=["transient_untrusted_markdown", "redacted_receipt"],
        side_effects=SideEffectLevel.read,
        risk_level=RiskLevel.high,
        authority_level=CapabilityAuthorityLevel.read_only,
        approval_required=True,
        deterministic=False,
        rollback_supported=True,
        receipt_required=True,
        privacy_level=CapabilityPrivacyLevel.local_private,
        estimated_cost_class=CapabilityCostClass.none,
        evidence_required=True,
        memory_write_allowed=False,
        context_injection_allowed=False,
        provider_runtime_allowed=True,
        browser_runtime_allowed=False,
        connector_write_allowed=False,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        concurrency_safe=False,
        runtime_policy=RuntimePolicy(
            timeout_seconds=60,
            max_retries=0,
            max_concurrency=1,
            deterministic=False,
        ),
        safety=SafetyPolicy(
            allow_parallel=False,
            approval_required=True,
            deny_untrusted_context=True,
            deny_if_unhealthy=True,
            max_risk_level=RiskLevel.high,
            max_side_effect_level=SideEffectLevel.read,
        ),
    )


def firecrawl_markdown_snapshot_from_state(
    state: WebProviderCapabilityState,
) -> CapabilityAvailabilitySnapshot:
    if (
        state.provider_ref != FIRECRAWL_SELF_HOSTED_PROVIDER_REF
        or state.deployment != WebProviderDeploymentKind.firecrawl_self_hosted
        or state.operation != WebProviderOperation.scrape_markdown
    ):
        raise ValueError("FIRECRAWL_CAPABILITY_STATE_SCOPE_MISMATCH")
    return build_capability_availability_snapshot(
        snapshot_ref=stable_web_hybrid_ref(
            "capability-availability-ref",
            {
                "state_ref": state.state_ref,
                "capability_ref": FIRECRAWL_MARKDOWN_CAPABILITY_REF,
            },
        ),
        capability_ref=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        provider_ref=state.provider_ref,
        adapter_ref=FIRECRAWL_MARKDOWN_ADAPTER_REF,
        catalog_status=state.catalog_status,
        compatibility_status=state.compatibility_status,
        configuration_status=state.configuration_status,
        health_status=state.health_status,
        authority_posture=state.authority_posture,
        resource_status=state.resource_status,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=state.safe_disable_status,
        checked_at=state.observed_at,
        expires_at=state.expires_at,
        freshness_status=state.freshness_status,
        declared_or_observed_version_ref=state.version_ref,
        reason_codes=list(state.reason_codes),
        blocker_codes=list(state.blocker_codes),
        evidence_refs=[state.state_ref],
        source_ref=state.state_ref,
        safe_summary=(
            "Self-hosted Firecrawl environment posture is separate from exact request authority."
        ),
    )


def execute_firecrawl_markdown(
    request: FirecrawlMarkdownRequest,
    *,
    capability_state: WebProviderCapabilityState,
    approval_authority: LocalApprovalAuthority,
    authority_leases: Sequence[AuthorityLease],
    transport: FirecrawlTransport | None = None,
    target_validator: TargetValidator | None = None,
    endpoint: FirecrawlConfiguredEndpoint | None = None,
    evaluated_at: datetime | None = None,
) -> FirecrawlMarkdownExecutionResult:
    now = evaluated_at or utc_now()
    snapshot = firecrawl_markdown_snapshot_from_state(capability_state)
    manifest = build_firecrawl_markdown_capability_manifest()
    task = TaskEnvelope(
        task_id=request.task_ref,
        user_request="Execute one exact governed one-page markdown extraction.",
        objective="Return transient untrusted markdown with redacted receipts.",
        selected_capability_ids=[FIRECRAWL_MARKDOWN_CAPABILITY_REF],
        context={"approval_ref": request.approval_ref} if request.approval_ref else {},
    )
    policy_context: dict[str, Any] = {
        "coordination_mode": CoordinationMode.direct_tool.value,
    }
    if request.approval_ref:
        policy_context["approval_ref"] = request.approval_ref
    local_approval_decision = approval_authority.validate_approval(
        manifest,
        task,
        policy_context,
    )
    policy_decision = PolicyEngine(approval_authority=approval_authority).can_execute(
        manifest, task, policy_context
    )

    exact_resource_refs = _exact_authority_resource_refs(request)
    authority_action = AuthorityActionRequest(
        action_ref=stable_web_hybrid_ref(
            "authority-action-ref",
            {"request_ref": request.request_ref, "task_ref": request.task_ref},
        ),
        domain=AuthorityDomain.browser,
        capability=AuthorityCapability.read,
        safe_summary="Evaluate one exact self-hosted markdown extraction attempt.",
        resource_refs=list(exact_resource_refs),
        capability_ref=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        lane_ref=FIRECRAWL_MARKDOWN_LANE_REF,
        adapter_ref=FIRECRAWL_MARKDOWN_ADAPTER_REF,
        rollback_ref="rollback-ref:web-access:firecrawl-markdown:stop-local-stack",
        safe_disable_ref="safe-disable-ref:web-access:firecrawl-markdown",
    )
    observed_authority_decision = evaluate_authority_request(
        authority_action,
        list(authority_leases),
        now=now,
    )
    authority_decision = (
        observed_authority_decision
        if authority_decision_has_exact_resource_scope(
            observed_authority_decision,
            authority_leases,
            exact_resource_refs,
        )
        else None
    )
    invocation_request = CapabilityInvocationRequest(
        request_ref=request.request_ref,
        snapshot_ref=snapshot.snapshot_ref,
        capability_ref=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        provider_ref=FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        adapter_ref=FIRECRAWL_MARKDOWN_ADAPTER_REF,
        task_ref=request.task_ref,
        approval_ref=request.approval_ref,
        authority_lease_required=True,
        local_approval_required=True,
        idempotency_posture=IdempotencyPosture.not_required,
        expected_execution_receipt_ref=request.expected_execution_receipt_ref,
    )
    invocation_decision = evaluate_capability_invocation(
        request=invocation_request,
        snapshot=snapshot,
        policy_decision=policy_decision,
        authority_decision=authority_decision,
        local_approval_decision=local_approval_decision,
        evaluated_at=now,
    )
    if invocation_decision.outcome != InvocationDecisionOutcome.allow:
        receipt = _transport_receipt(
            request=request,
            invocation_decision=invocation_decision,
            status=WebProviderTransportStatus.blocked,
            reason_codes=tuple(
                dict.fromkeys(
                    (
                        *invocation_decision.blocker_codes,
                        *invocation_decision.reason_codes,
                    )
                )
            ),
            network_call_performed=False,
            evidence=None,
            created_at=now,
        )
        return _execution_result(
            request=request,
            invocation_decision=invocation_decision,
            receipt=receipt,
            evidence=None,
            reason_codes=tuple(invocation_decision.reason_codes),
            blocker_codes=tuple(invocation_decision.blocker_codes),
        )

    attempt = execute_authorized_firecrawl_markdown_attempt(
        request=request,
        invocation_decision=invocation_decision,
        capability_ref=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        provider_ref=FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        adapter_ref=FIRECRAWL_MARKDOWN_ADAPTER_REF,
        transport=transport or build_loopback_firecrawl_transport(endpoint),
        target_validator=target_validator or validate_resolved_public_target,
    )
    receipt = _transport_receipt(
        request=request,
        invocation_decision=invocation_decision,
        status=attempt.status,
        reason_codes=attempt.reason_codes,
        network_call_performed=attempt.network_call_performed,
        evidence=attempt.evidence,
        created_at=now,
    )
    return _execution_result(
        request=request,
        invocation_decision=invocation_decision,
        receipt=receipt,
        evidence=attempt.evidence,
        reason_codes=attempt.reason_codes,
        blocker_codes=()
        if attempt.status == WebProviderTransportStatus.succeeded
        else attempt.reason_codes,
    )


def execute_authorized_firecrawl_markdown_attempt(
    *,
    request: FirecrawlMarkdownRequest,
    invocation_decision: CapabilityInvocationDecision,
    capability_ref: str,
    provider_ref: str,
    adapter_ref: str,
    transport: FirecrawlTransport,
    target_validator: TargetValidator,
) -> FirecrawlMarkdownAttemptResult:
    adapter = _FirecrawlMarkdownAdapter(
        extract_request=request,
        invocation_decision=invocation_decision,
        capability_ref=capability_ref,
        provider_ref=provider_ref,
        adapter_ref=adapter_ref,
        transport=transport,
        target_validator=target_validator,
    )
    gateway = WebAccessGateway(
        policy=WebAccessPolicy(allow_firecrawl_markdown_extract=True),
        adapters={WebAccessRequestKind.EXTRACT_MARKDOWN: adapter},
    )
    gateway_result = gateway.execute(
        WebAccessRequest(
            kind=WebAccessRequestKind.EXTRACT_MARKDOWN,
            url=request.target_url,
            method="GET",
            authority_mode=WebAccessAuthorityMode.READ_ONLY,
            network_lane=WebAccessNetworkLane.AGENT_PUBLIC_WEB,
            allowed_domains=request.allowed_domains,
            metadata={
                "format": "markdown",
                "page_count": request.page_count,
                "attempt_count": request.attempt_count,
                "max_markdown_chars": request.max_markdown_chars,
                "target_source_ref": request.target_source_ref,
            },
            request_id=request.request_ref,
        )
    )
    payload = (
        gateway_result.evidence_bundle.payload
        if gateway_result.evidence_bundle is not None
        else {}
    )
    status = _transport_status(payload, gateway_result.status)
    raw_evidence = payload.get("evidence")
    evidence = (
        FirecrawlMarkdownEvidence.model_validate(raw_evidence)
        if isinstance(raw_evidence, Mapping)
        and status
        in {WebProviderTransportStatus.succeeded, WebProviderTransportStatus.simulated}
        else None
    )
    reason_codes = _safe_reason_codes(payload.get("reason_codes"))
    network_call_performed = payload.get("network_call_performed") is True
    return FirecrawlMarkdownAttemptResult(
        status=status,
        evidence=evidence,
        reason_codes=reason_codes,
        network_call_performed=network_call_performed,
        gateway_audit_ref=stable_web_hybrid_ref(
            "web-access-audit-ref",
            {
                "request_ref": request.request_ref,
                "invocation_decision_ref": invocation_decision.decision_ref,
                "capability_ref": capability_ref,
                "provider_ref": provider_ref,
                "adapter_ref": adapter_ref,
            },
        ),
    )


class _FirecrawlMarkdownAdapter:
    adapter_kind = WebAccessAdapterKind.FIRECRAWL

    def __init__(
        self,
        *,
        extract_request: FirecrawlMarkdownRequest,
        invocation_decision: CapabilityInvocationDecision,
        capability_ref: str,
        provider_ref: str,
        adapter_ref: str,
        transport: FirecrawlTransport,
        target_validator: TargetValidator,
    ) -> None:
        self._extract_request = extract_request
        self._invocation_decision = invocation_decision
        self._capability_ref = capability_ref
        self._provider_ref = provider_ref
        self._adapter_ref = adapter_ref
        self._transport = transport
        self._target_validator = target_validator
        self._use_lock = threading.Lock()
        self._used = False

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        with self._use_lock:
            if self._used:
                return _adapter_failure(
                    "FIRECRAWL_INVOCATION_DECISION_REPLAY_DENIED",
                    False,
                )
            self._used = True
        invocation_scope_matches = (
            self._invocation_decision.outcome == InvocationDecisionOutcome.allow
            and self._invocation_decision.cache_posture == "not_cacheable"
            and self._invocation_decision.request_ref
            == self._extract_request.request_ref
            and self._invocation_decision.capability_ref
            == self._capability_ref
            and self._invocation_decision.provider_ref
            == self._provider_ref
            and self._invocation_decision.adapter_ref == self._adapter_ref
            and self._invocation_decision.authority_decision_ref is not None
            and self._invocation_decision.approval_decision_ref is not None
        )
        if (
            not decision.allowed
            or request.request_id != self._extract_request.request_ref
            or not invocation_scope_matches
        ):
            return _adapter_failure("FIRECRAWL_GATEWAY_SCOPE_MISMATCH", False)
        live_transport = bool(
            getattr(self._transport, "real_world_transport_performed", False)
        )
        try:
            self._target_validator(self._extract_request.target_url)
        except FirecrawlTransportError as exc:
            return _adapter_failure(exc.code, False)
        except Exception:  # noqa: BLE001 - target validation details stay private.
            return _adapter_failure("FIRECRAWL_TARGET_VALIDATION_FAILED", False)
        try:
            payload = self._transport(self._extract_request)
            evidence = _normalize_provider_payload(
                payload,
                request=self._extract_request,
                target_validator=self._target_validator,
            )
        except FirecrawlTransportError as exc:
            return _adapter_failure(
                exc.code,
                exc.network_call_performed and live_transport,
            )
        except Exception:  # noqa: BLE001 - provider boundary must not leak details.
            return _adapter_failure(
                "FIRECRAWL_PROVIDER_TRANSPORT_FAILED", live_transport
            )
        status = (
            WebProviderTransportStatus.succeeded
            if live_transport
            else WebProviderTransportStatus.simulated
        )
        return {
            "allowed": True,
            "status": status.value,
            "summary": "Firecrawl returned bounded transient untrusted markdown evidence.",
            "reason_codes": ("FIRECRAWL_MARKDOWN_EXTRACTION_COMPLETED",),
            "evidence": evidence.model_dump(mode="json"),
            "sources": [
                SourceMetadata(
                    url=evidence.target_url,
                    final_url=evidence.final_url,
                    host=evidence.host,
                    source_type="extracted_markdown",
                    authority="untrusted_web_evidence",
                    allowed_methods=("GET",),
                    fetched_at=utc_now(),
                    content_hash=evidence.content_hash_ref,
                    content_untrusted=True,
                    notes=("instructions_denied", "transient_markdown_only"),
                )
            ],
            "network_call_performed": live_transport,
            "raw_target_stored": False,
            "raw_provider_payload_stored": False,
        }


def _adapter_failure(code: str, network_call_performed: bool) -> Mapping[str, Any]:
    return {
        "allowed": False,
        "status": WebProviderTransportStatus.failed.value,
        "summary": "Firecrawl extraction failed closed with no provider payload retained.",
        "reason_codes": (code,),
        "sources": [],
        "network_call_performed": network_call_performed,
        "raw_target_stored": False,
        "raw_provider_payload_stored": False,
    }


def _normalize_provider_payload(
    payload: Mapping[str, Any],
    *,
    request: FirecrawlMarkdownRequest,
    target_validator: TargetValidator,
) -> FirecrawlMarkdownEvidence:
    if payload.get("success") is not True:
        raise FirecrawlTransportError(
            "FIRECRAWL_PROVIDER_REPORTED_FAILURE",
            network_call_performed=True,
        )
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise FirecrawlTransportError(
            "FIRECRAWL_PROVIDER_DATA_OBJECT_REQUIRED",
            network_call_performed=True,
        )
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise FirecrawlTransportError(
            "FIRECRAWL_MARKDOWN_REQUIRED",
            network_call_performed=True,
        )
    if len(markdown) > request.max_markdown_chars:
        raise FirecrawlTransportError(
            "FIRECRAWL_MARKDOWN_LIMIT_EXCEEDED",
            network_call_performed=True,
        )
    metadata = data.get("metadata")
    if not isinstance(metadata, Mapping):
        raise FirecrawlTransportError(
            "FIRECRAWL_METADATA_REQUIRED",
            network_call_performed=True,
        )
    source_url = metadata.get("sourceURL", request.target_url)
    final_url = metadata.get("url", source_url)
    if not isinstance(source_url, str) or not isinstance(final_url, str):
        raise FirecrawlTransportError(
            "FIRECRAWL_FINAL_URL_REQUIRED",
            network_call_performed=True,
        )
    if source_url != request.target_url or final_url != request.target_url:
        raise FirecrawlTransportError(
            "FIRECRAWL_TARGET_REDIRECT_DENIED",
            network_call_performed=True,
        )
    final_host = _validated_target_syntax(final_url)
    if not _host_matches_allowed_domains(final_host, request.allowed_domains):
        raise FirecrawlTransportError(
            "FIRECRAWL_FINAL_HOST_NOT_ALLOWED",
            network_call_performed=True,
        )
    target_validator(final_url)
    status_code = metadata.get("statusCode")
    if status_code is not None and (
        not isinstance(status_code, int)
        or isinstance(status_code, bool)
        or not 200 <= status_code <= 299
    ):
        raise FirecrawlTransportError(
            "FIRECRAWL_TARGET_NON_SUCCESS_STATUS",
            network_call_performed=True,
        )
    preview, preview_status = _redacted_preview(markdown)
    return FirecrawlMarkdownEvidence(
        source_ref=request.target_source_ref,
        target_url=request.target_url,
        final_url=final_url,
        host=final_host,
        title=_bounded_untrusted_text(metadata.get("title"), limit=240),
        markdown=markdown,
        content_hash_ref=_markdown_hash_ref(markdown),
        bounded_redacted_preview=preview,
        preview_redaction_status=preview_status,
    )


def _redacted_preview(markdown: str) -> tuple[str, FirecrawlPreviewRedactionStatus]:
    redacted = redact_debug_text(markdown, max_chars=500)
    preview = " ".join(redacted.preview.split())
    if contains_secret_like(preview) or contains_obvious_secret(preview):
        return (
            "Untrusted markdown preview withheld by redaction policy.",
            FirecrawlPreviewRedactionStatus.withheld,
        )
    status = (
        FirecrawlPreviewRedactionStatus.redacted
        if redacted.redactions_applied
        else FirecrawlPreviewRedactionStatus.bounded
    )
    return preview or "Untrusted markdown contained no previewable text.", status


def validate_resolved_public_target(url: str) -> None:
    host = _validated_target_syntax(url)
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FirecrawlTransportError(
            "FIRECRAWL_TARGET_DNS_RESOLUTION_FAILED",
            network_call_performed=False,
        ) from exc
    addresses = {str(info[4][0]) for info in infos if info[4]}
    if not addresses or any(
        not ipaddress.ip_address(value).is_global for value in addresses
    ):
        raise FirecrawlTransportError(
            "FIRECRAWL_TARGET_PRIVATE_OR_LOCAL_DENIED",
            network_call_performed=False,
        )


def firecrawl_target_source_ref(url: str) -> str:
    return f"web-source-ref:sha256:{hashlib.sha256(url.encode('utf-8')).hexdigest()}"


def _markdown_hash_ref(markdown: str) -> str:
    return f"content-hash-ref:sha256:{hashlib.sha256(markdown.encode('utf-8')).hexdigest()}"


def _validated_target_syntax(url: str) -> str:
    parts = urlsplit(url)
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("FIRECRAWL_TARGET_URL_INVALID") from exc
    host = (parts.hostname or "").lower().rstrip(".")
    if (
        parts.scheme != "https"
        or not host
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or port not in {None, 443}
        or not _public_domain(host)
    ):
        raise ValueError("FIRECRAWL_TARGET_URL_INVALID")
    return host


def _public_domain(value: str) -> bool:
    if not value or value == "localhost" or value.endswith((".local", ".internal")):
        return False
    try:
        return ipaddress.ip_address(value).is_global
    except ValueError:
        return "." in value


def _host_matches_allowed_domains(host: str, allowed_domains: tuple[str, ...]) -> bool:
    return any(
        host == domain or host.endswith(f".{domain}") for domain in allowed_domains
    )


def _bounded_untrusted_text(value: Any, *, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    normalized = "".join(
        char if ord(char) >= 32 and ord(char) != 127 else " " for char in value
    )
    return " ".join(normalized.split())[:limit]


def _exact_authority_resource_refs(
    request: FirecrawlMarkdownRequest,
) -> tuple[str, ...]:
    return (
        request.request_ref,
        request.task_ref,
        request.target_source_ref,
        FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        FIRECRAWL_MARKDOWN_ADAPTER_REF,
    )


def authority_decision_has_exact_resource_scope(
    decision: AuthorityPolicyDecision,
    leases: Sequence[AuthorityLease],
    exact_resource_refs: tuple[str, ...],
) -> bool:
    if not decision.lease_ref:
        return False
    lease = next(
        (item for item in leases if item.lease_ref == decision.lease_ref), None
    )
    if lease is None:
        return False
    required = set(exact_resource_refs)
    for constraint in lease.authority_constraints:
        if (
            AuthorityConstraintKind(constraint.kind)
            != AuthorityConstraintKind.resource_refs
        ):
            continue
        if set(constraint.allowed_refs) != required:
            continue
        return constraint.constraint_ref in decision.applied_constraint_refs
    return False


def _transport_status(
    payload: Mapping[str, Any],
    gateway_status: WebAccessPolicyStatus,
) -> WebProviderTransportStatus:
    if gateway_status != WebAccessPolicyStatus.ALLOWED:
        if payload.get("status") == WebProviderTransportStatus.failed.value:
            return WebProviderTransportStatus.failed
        return WebProviderTransportStatus.blocked
    try:
        return WebProviderTransportStatus(str(payload.get("status")))
    except ValueError:
        return WebProviderTransportStatus.failed


def _safe_reason_codes(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ("FIRECRAWL_PROVIDER_RESULT_INVALID",)
    codes = tuple(dict.fromkeys(str(item) for item in value))
    if not codes or any(not _SAFE_CODE.fullmatch(code) for code in codes):
        return ("FIRECRAWL_PROVIDER_RESULT_INVALID",)
    return codes


def _transport_receipt(
    *,
    request: FirecrawlMarkdownRequest,
    invocation_decision: CapabilityInvocationDecision,
    status: WebProviderTransportStatus,
    reason_codes: tuple[str, ...],
    network_call_performed: bool,
    evidence: FirecrawlMarkdownEvidence | None,
    created_at: datetime,
) -> WebProviderTransportReceipt:
    return WebProviderTransportReceipt(
        receipt_ref=stable_web_hybrid_ref(
            "web-provider-transport-receipt-ref",
            {
                "request_ref": request.request_ref,
                "invocation_decision_ref": invocation_decision.decision_ref,
                "status": status.value,
                "content_hash_ref": evidence.content_hash_ref if evidence else None,
            },
        ),
        request_ref=request.request_ref,
        provider_ref=FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
        deployment=WebProviderDeploymentKind.firecrawl_self_hosted,
        operation=WebProviderOperation.scrape_markdown,
        target_source_ref=request.target_source_ref,
        configured_endpoint_ref=FIRECRAWL_SELF_HOSTED_ENDPOINT_REF,
        target_method="GET",
        provider_transport_method=WebProviderTransportMethod.post,
        request_schema_ref=FIRECRAWL_MARKDOWN_REQUEST_SCHEMA_REF,
        status=status,
        response_receipt_hash_ref=evidence.content_hash_ref if evidence else None,
        authority_decision_ref=(
            invocation_decision.authority_decision_ref
            or "authority-decision-ref:firecrawl-markdown:missing"
        ),
        approval_decision_ref=(
            invocation_decision.approval_decision_ref
            or "approval-decision-ref:firecrawl-markdown:missing"
        ),
        budget_decision_ref=FIRECRAWL_NOT_METERED_BUDGET_REF,
        reason_codes=reason_codes,
        network_call_performed=network_call_performed,
        created_at=created_at,
    )


def _execution_result(
    *,
    request: FirecrawlMarkdownRequest,
    invocation_decision: CapabilityInvocationDecision,
    receipt: WebProviderTransportReceipt,
    evidence: FirecrawlMarkdownEvidence | None,
    reason_codes: tuple[str, ...],
    blocker_codes: tuple[str, ...],
) -> FirecrawlMarkdownExecutionResult:
    return FirecrawlMarkdownExecutionResult(
        request_ref=request.request_ref,
        task_ref=request.task_ref,
        invocation_decision=invocation_decision,
        transport_receipt=receipt,
        gateway_audit_ref=stable_web_hybrid_ref(
            "web-access-audit-ref",
            {
                "request_ref": request.request_ref,
                "invocation_decision_ref": invocation_decision.decision_ref,
                "transport_receipt_ref": receipt.receipt_ref,
            },
        ),
        status=receipt.status,
        evidence=evidence,
        execution_succeeded=receipt.status == WebProviderTransportStatus.succeeded,
        reason_codes=reason_codes,
        blocker_codes=blocker_codes,
    )


__all__ = [
    "FIRECRAWL_MARKDOWN_ADAPTER_REF",
    "FIRECRAWL_MARKDOWN_CAPABILITY_REF",
    "FIRECRAWL_MARKDOWN_LANE_REF",
    "FIRECRAWL_SELF_HOSTED_DEFAULT_ENDPOINT",
    "FIRECRAWL_SELF_HOSTED_ENDPOINT_REF",
    "FIRECRAWL_SELF_HOSTED_PROVIDER_REF",
    "FirecrawlConfiguredEndpoint",
    "FirecrawlMarkdownEvidence",
    "FirecrawlMarkdownAttemptResult",
    "FirecrawlMarkdownExecutionResult",
    "FirecrawlMarkdownRequest",
    "FirecrawlPreviewRedactionStatus",
    "FirecrawlTransportError",
    "build_firecrawl_markdown_capability_manifest",
    "build_loopback_firecrawl_transport",
    "authority_decision_has_exact_resource_scope",
    "execute_firecrawl_markdown",
    "execute_authorized_firecrawl_markdown_attempt",
    "firecrawl_markdown_snapshot_from_state",
    "firecrawl_target_source_ref",
    "validate_resolved_public_target",
]
